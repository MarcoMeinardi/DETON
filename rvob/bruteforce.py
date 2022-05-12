import argparse
from os import path
import json
from ast import literal_eval
from multiprocessing import Pool
import time

from logger import *
from configuration import Configuration
from worker import Worker

def get_args():
    parser = argparse.ArgumentParser(description="Bruteforce of DETON")

    parser.add_argument(
        "-f", "-in", "--file",
        metavar="input file",
        help="The path of the file in .json format to process",
        required=True,
        type=str)

    parser.add_argument(
        "-w", "--optimize",
        metavar="What to optimize",
        help="If you want to optimize for overhead or heat",
        choices=["heat", "overhead"],
        required=True,
        type=str)

    parser.add_argument(
        "-O", "--overhead",
        metavar="Max overhead value or overhead upper bound",
        help="The maximum Overhead value wanted, in percentage, compared to the original file or the upper bound for the overhead optimization",
        required=True,
        type=int)

    parser.add_argument(
        "-H", "--heat",
        metavar="Target heat",
        help="The target mean heat, in percentage, to search for, while minimizing the overhead (required only if optimizing for overhead)",
        required=False,
        type=int)

    parser.add_argument(
        "-t", "--threads",
        metavar="Number of thread to use",
        help="The number of max thread wanted to be used",
        required=False,
        default='1',
        type=int)

    parser.add_argument(
        "-o", "--output",
        metavar="output file",
        help="The path of the file where all the attempted configurations should be saved in .json format",
        required=False,
        default=path.dirname(__file__) + '/metrics/configurations.json',
        type=str)

    parser.add_argument(
        "-l", "--log-level",
        metavar="logging level",
        help="The verbosity of the logs (debug, info, warning, error)",
        required=False,
        default='debug',
        type=str)

    return parser.parse_args()

def save_if_best(configuration):
    global best, original_configuration, total_iterations, all_configurations
    Log.debug(f"Executed with: {configuration} ({configuration.id} / {total_iterations})")
    Log.debug("New mean heat:", configuration.mean_heat)
    Log.debug("Overhead introduced:", configuration.lines_num - original_configuration.lines_num)
    Log.debug()
    if configuration.mean_heat > best.mean_heat:
        best = configuration

    configuration_dict = configuration.__dict__.copy()
    del configuration_dict["input_data"]
    all_configurations["all"].append(configuration_dict)
    
def preprocess_configurations(todo_configurations, max_overhead, input_data):
    # Calculate total iterations
    max_overhead += 1
    iteration = 0
    for constant_obfuscation in range(0, max_overhead):
        for obfuscation_chain_length in range(2, max(3, max_overhead)):
            if constant_obfuscation * obfuscation_chain_length >= max_overhead: break

            for garbage_blocks in range(0, max_overhead):
                for garbage_length in range(1, max(2, max_overhead)):
                    if constant_obfuscation * obfuscation_chain_length + garbage_blocks * garbage_length >= max_overhead: break

                    if constant_obfuscation == 0: obfuscation_chain_length = 0
                    if garbage_blocks == 0: garbage_length = 0

                    register_scrumbling = max_overhead - constant_obfuscation * obfuscation_chain_length - garbage_blocks * garbage_length - 1
                    iteration += 1
                    configuration = Configuration(
                        input_data, 
                        register_scrumbling, 
                        constant_obfuscation, 
                        obfuscation_chain_length, 
                        garbage_blocks, 
                        garbage_length,
                        iteration
                    )
                    todo_configurations.append(configuration)

                    if garbage_blocks == 0: break
            if constant_obfuscation == 0: break

    return iteration

def main():
    start_time = time.time()
    global best, original_configuration, total_iterations, all_configurations
    args = get_args()

    args.log_level = args.log_level.upper()
    if args.log_level not in log_dict:
        Log.error(f"Logging level {args.log_level} doesn't exists")
        return
    else:
        Log.log_level = log_dict[args.log_level]

    input_file = args.file
    threads = args.threads
    configurations_file = args.output
    no_main = {'patricia': 'bit', 'sha': 'sha_transform', 'bitarray': 'alloc_bit_array', 'idea': 'mulInv', 'rsa': 'mpi_add'}
    if path.basename(input_file).split(".")[0] in no_main:
        input_data = (input_file, no_main[path.basename(input_file).split(".")[0]])
    else:
        input_data = (input_file, '')

    original_configuration = Configuration(input_data, 0, 0, 0, 0, 0, "original")
    original_configuration.evaluate()
    Log.info("Original mean heat:", original_configuration.mean_heat)

    original_configuration_dict = original_configuration.__dict__.copy()
    del original_configuration_dict["input_data"]
    all_configurations = {
        "best": None,
        "original": original_configuration_dict,
        "file": input_data[0],
        "total_time": -1,
        "threads": threads,
        "all": []
    }

    max_overhead = args.overhead * original_configuration.lines_num // 100
    if args.optimize == "heat":
        Log.info("Max absolute overhead:", max_overhead)
        best = original_configuration

        todo_configurations = []
        total_iterations = preprocess_configurations(todo_configurations, max_overhead, input_data)

        worker = Worker(
            configurations=todo_configurations,
            optimize_overhead=False,
            target_heat=None,
            original_configuration=original_configuration,
            configurations_backup=all_configurations["all"],
            n_threads=threads,
            Log=Log
        )
        best = worker.run()
    else:
        if args.heat is None:
            Log.error("Target heat must be specified while optimizing for overhead")
            return
        best = None
        target_heat = args.heat * original_configuration.mean_heat / 100
        Log.info(f"Target heat: {target_heat}")
        left = 0
        right = max_overhead + 1
        while left <= right:
            actual_overhead = left + (right - left) // 2
            Log.info(f"Bounds: ({left}:{right} -> {actual_overhead})")  #should be debug, but debug is too verbose
            todo_configurations = []
            total_iterations = preprocess_configurations(todo_configurations, actual_overhead, input_data)

            worker = Worker(
                configurations=todo_configurations,
                optimize_overhead=True,
                target_heat=target_heat,
                original_configuration=original_configuration,
                configurations_backup=all_configurations["all"],
                n_threads=threads,
                Log=Log
            )
            maybe_best = worker.run()
            if maybe_best is None:
                left = actual_overhead + 1
            else:
                best = maybe_best  # this might not be the best solution for this overhead, it may be worth running the whole process with this overhead (todo: cache already done configurations)
                right = actual_overhead - 1

        if best is None:
            Log.error("Either you lied to me :D or DETON is too stupidly random")
            Log.error(f"No configuration found with (absolute) heat >= {target_heat} and (absolute) overhead <= {max_overhead}")
            return


    stop_time = time.time()
    total_time = stop_time - start_time
    Log.info()
    Log.info(f"DONE (Total time: {total_time:.3f} s)")
    Log.info("-" * 40)
    Log.info("Best parameters:")
    Log.info("Register scrambling:", best.register_scrumbling)
    Log.info("Constant obfuscation:", best.constant_obfuscation)
    Log.info("Obfuscation chain length:", best.obfuscation_chain_length)
    Log.info("Garbage blocks:", best.garbage_blocks)
    Log.info("Garbage length:", best.garbage_length)
    Log.info()
    Log.info("Original mean heat:", original_configuration.mean_heat)
    Log.info(f"Best mean heat: {best.mean_heat} ({best.mean_heat / original_configuration.mean_heat * 100:.3f} %)")
    Log.info(f"Overhead introduced: {best.lines_num - original_configuration.lines_num} ({(best.lines_num - original_configuration.lines_num) / original_configuration.lines_num * 100:.3f} %)")
    Log.info("-" * 40)

    # Save best run
    best.id = "best"
    best.evaluate()

    best_configuration_dict = best.__dict__.copy()
    del best_configuration_dict["input_data"]
    all_configurations["best"] = best_configuration_dict
    all_configurations["total_time"] = total_time
    all_configurations["all"].sort(key = lambda x: x["id"])

    with open(configurations_file, "w") as f:
        f.write(json.dumps(all_configurations))

if __name__ == "__main__":
    main()