import argparse
from os import access, path
import json
from ast import literal_eval
from multiprocessing import Pool
import sys

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
        metavar="Max overhead value or overhead lower bound",
        help="The maximum tolerable overhead value, in percentage, compared to the original file or the lower bound for the overhead optimization search",
        required=False,
        type=int)

    parser.add_argument(
        "-H", "--heat",
        metavar="Target heat",
        # Percentage heat wouldn't make much sense, because the initial heat varies, because of randomness
        help="The absolute target mean heat to search for, while minimizing the overhead",
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
        "-o", "--output", "-out",
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
        default='info',
        type=str)

    return parser.parse_args()
    
def preprocess_configurations(todo_configurations, max_overhead, input_data):
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

def show_and_save_best(best, original, all_configurations, configurations_file, total_time):
    Log.info()
    Log.info(f"DONE (CPU time: {total_time:.3f} s)")
    Log.info("-" * 40)
    Log.info("Best parameters:")
    Log.info("Register scrambling:", best.register_scrumbling)
    Log.info("Constant obfuscation:", best.constant_obfuscation)
    Log.info("Obfuscation chain length:", best.obfuscation_chain_length)
    Log.info("Garbage blocks:", best.garbage_blocks)
    Log.info("Garbage length:", best.garbage_length)
    Log.info()
    Log.info("Original mean heat:", original.mean_heat)
    Log.info(f"Best mean heat: {best.mean_heat} ({best.mean_heat / original.mean_heat * 100:.3f} %)")
    Log.info(f"Overhead introduced: {best.lines_num - original.lines_num} ({(best.lines_num - original.lines_num) / original.lines_num * 100:.3f} %)")
    Log.info("-" * 40)

    # Save best run
    best.id = "best"
    best.evaluate()

    best_configuration_dict = best.__dict__.copy()
    del best_configuration_dict["input_data"]
    all_configurations["best"] = best_configuration_dict
    all_configurations["CPU_time"] = total_time
    all_configurations["all"].sort(key = lambda x: x["id"])

    with open(configurations_file, "w") as f:
        f.write(json.dumps(all_configurations))

def main():
    args = get_args()

    args.log_level = args.log_level.upper()
    if args.log_level not in log_dict:
        Log.error(f"Logging level {args.log_level} doesn't exists")
        return
    else:
        Log.log_level = log_dict[args.log_level]

    if args.optimize == "overhead" and args.heat is None:
        Log.error("Target heat must be specified while optimizing for overhead")
        return
    if args.optimize == "heat" and args.overhead is None:
        Log.error("Target overhead must be specified while optimizing for heat")
        return

    if args.optimize == "overhead" and args.heat > 27:
        Log.warning("Heat >= 27 would probably not be found, this program may run forever")

    input_file = args.file
    threads = args.threads
    configurations_file = args.output
    no_main = {'patricia': 'bit', 'sha': 'sha_transform', 'bitarray': 'alloc_bit_array', 'idea': 'mulInv', 'rsa': 'mpi_add'}
    if path.basename(input_file).split(".")[0] in no_main:
        input_data = (input_file, no_main[path.basename(input_file).split(".")[0]])
    else:
        input_data = (input_file, '')

    original = Configuration(input_data, 0, 0, 0, 0, 0, "original")
    original.evaluate()
    Log.info(f"Original mean heat: {original.mean_heat:.3f}")

    original_dict = original.__dict__.copy()
    del original_dict["input_data"]
    all_configurations = {
        "best": None,
        "original": original_dict,
        "file": input_data[0],
        "total_time": -1,
        "threads": threads,
        "command": sys.argv[1:],
        "all": []
    }

    if args.optimize == "heat":
        max_overhead = args.overhead * original.lines_num // 100
        Log.info("Max absolute overhead:", max_overhead)
        Log.info()
        best = original

        todo_configurations = []
        preprocess_configurations(todo_configurations, max_overhead, input_data)

        worker = Worker(
            configurations=todo_configurations,
            optimize_overhead=False,
            target_heat=None,
            original=original,
            configurations_backup=all_configurations["all"],
            n_threads=threads,
            Log=Log
        )
        best = worker.run()

    else:  # optimize for overhead
        best = None
        target_heat = args.heat
        Log.info(f"Target heat: {target_heat:.3f}")
        Log.info()

        # start from 1% and multiply times two, until the required heat is reached,
        # than binary search between the first hit and the last miss, to get the minimum overhead
        if args.overhead is None:
            actual_overhead_percentage = 1
        else:
            actual_overhead_percentage = args.overhead

        hit = False
        last_miss = 0
        while not hit:
            actual_overhead = actual_overhead_percentage * original.lines_num // 100
            Log.info(f"Trying with overhead = {actual_overhead_percentage} %  ({actual_overhead})")
            todo_configurations = []
            preprocess_configurations(todo_configurations, actual_overhead, input_data)

            worker = Worker(
                configurations=todo_configurations,
                optimize_overhead=True,
                target_heat=target_heat,
                original=original,
                configurations_backup=all_configurations["all"],
                n_threads=threads,
                Log=Log
            )
            maybe_best = worker.run()
            if maybe_best is not None:
                hit = True
                first_hit = actual_overhead_percentage
                best = maybe_best
            else:
                last_miss = actual_overhead_percentage
                actual_overhead_percentage *= 2

        Log.info(f"First configuration with heat >= {args.heat} found")
        right = first_hit - 1
        left = min(last_miss + 1, right)  # I think this is needed just for 0 % overhead
        already_done = set()  # for small programs, close percentage may lead to the same absolute overhead

        while left <= right:
            actual_overhead_percentage = left + (right - left) // 2
            actual_overhead = actual_overhead_percentage * original.lines_num // 100
            if actual_overhead in already_done:
                break  # if this happens, left is close enought to right to make it always happen
            Log.info(f"Bounds: [{left} % : {right} %] -> {actual_overhead}")
            todo_configurations = []
            preprocess_configurations(todo_configurations, actual_overhead, input_data)

            worker = Worker(
                configurations=todo_configurations,
                optimize_overhead=True,
                target_heat=target_heat,
                original=original,
                configurations_backup=all_configurations["all"],
                n_threads=threads,
                Log=Log
            )
            maybe_best = worker.run()
            if maybe_best is None:
                left = actual_overhead_percentage + 1
            else:
                best = maybe_best  # this might not be the best solution for this overhead, it may be worth running the whole process with this overhead (todo: cache already done configurations)
                right = actual_overhead_percentage - 1

        assert best is not None, "Wait?!?! This cannot happen!"

    total_time = sum(configuration["running_time"] for configuration in all_configurations["all"])

    show_and_save_best(best, original, all_configurations, configurations_file, total_time)


if __name__ == "__main__":
    main()