import argparse
from os import path
import re
from ast import literal_eval
from deton import execute
from multiprocessing import Pool


class Configuration:
    def __init__(self, input_file, register_scrumbling, constant_obfuscation, obfuscation_chain_length, garbage_blocks, garbage_length, id):
        self.input_file = input_file
        self.register_scrumbling = register_scrumbling
        self.constant_obfuscation = constant_obfuscation
        self.obfuscation_chain_length = obfuscation_chain_length
        self.garbage_blocks = garbage_blocks
        self.garbage_length = garbage_length
        self.id = id

    def get_parameters(self):
        return (
            self.input_file, 
            self.register_scrumbling, 
            self.constant_obfuscation, 
            self.obfuscation_chain_length, 
            self.garbage_blocks, 
            self.garbage_length
        )

    def evaluate(self):
        if isinstance(self.id, int):
            output_name = str(self.id % 20) # to avoid generating thousands of files, but also avoid file collision in parallel threads
        else:
            output_name = self.id

        execute(
            self.input_file, "", 50, 
            self.register_scrumbling, self.constant_obfuscation, self.obfuscation_chain_length, self.garbage_blocks, self.garbage_length,
            path.dirname(__file__) + f"/metrics/output_{output_name}.s", False, True, f"_{output_name}"
        )
        with open(path.dirname(__file__) + f"/metrics/data_metrics_{output_name}.txt") as f:
            data = f.read()
            
        mean_heats = literal_eval(re.search(r"Mean heat after: (\[.*\])", data).group(1))
        self.mean_heat = sum(mean_heats) / 32

        with open(path.dirname(__file__) + f"/metrics/output_{output_name}.s") as f:
            self.lines_num = f.read().count("\n")
        
        return self

    def __str__(self):
        return f"{self.register_scrumbling} {self.constant_obfuscation} {self.obfuscation_chain_length} {self.garbage_blocks} {self.garbage_length}"


def get_args():
    parser = argparse.ArgumentParser(description="Bruteforce of DETON")

    parser.add_argument(
        "Overhead",
        metavar="Max overhead value",
        help="The maximum Overhead value wanted in % compared to the original file",
        default='50',
        type=int)

    parser.add_argument(
        "File",
        metavar="File path input",
        help="The path of the file in .json format to process",
        default='q',
        type=str)

    parser.add_argument(
        "Threads",
        metavar="Number of thread to use",
        help="The number of max thread wanted to be used",
        nargs='?',
        default='1',
        type=int)

    return parser.parse_args()

def save_if_best(configuration):
    global best, original_configuration, total_iterations
    print(f"Executed with: {configuration} ({configuration.id} / {total_iterations})")
    print("New mean heat:", configuration.mean_heat)
    print("Overhead introduced:", configuration.lines_num - original_configuration.lines_num)
    print()
    if configuration.mean_heat > best.mean_heat:
        best = configuration
    

def main():
    global best, original_configuration, total_iterations
    args = get_args()
    input_file = args.File
    threads = args.Threads

    original_configuration = Configuration(input_file, 0, 0, 0, 0, 0, "original")
    original_configuration.evaluate()
    best = original_configuration
    max_overhead = args.Overhead * original_configuration.lines_num // 100
    print("Max absolute overhead:", max_overhead)
    print("Original mean heat:", original_configuration.mean_heat)
    print()

    # Calculate total iterations
    max_overhead += 1
    total_iterations = 0
    for constant_obfuscation in range(0, max_overhead):
        for obfuscation_chain_length in range(2, max(3, max_overhead)):
            if constant_obfuscation * obfuscation_chain_length >= max_overhead: break

            for garbage_blocks in range(0, max_overhead):
                for garbage_length in range(1, max(2, max_overhead)):
                    if constant_obfuscation * obfuscation_chain_length + garbage_blocks * garbage_length >= max_overhead: break

                    total_iterations += 1

                    if garbage_blocks == 0: break
            if constant_obfuscation == 0: break

    # Try every combination
    iteration = 0
    thread_pool = Pool(threads)

    for constant_obfuscation in range(0, max_overhead):
        for obfuscation_chain_length in range(2, max(3, max_overhead)):
            if constant_obfuscation * obfuscation_chain_length >= max_overhead: break

            for garbage_blocks in range(0, max_overhead):
                for garbage_length in range(1, max(2, max_overhead)):
                    if constant_obfuscation * obfuscation_chain_length + garbage_blocks * garbage_length >= max_overhead: break

                    if constant_obfuscation == 0: obfuscation_chain_length = 0
                    if garbage_blocks == 0: garbage_length = 0

                    register_scrumbling = max_overhead - constant_obfuscation * obfuscation_chain_length - garbage_blocks * garbage_length
                    iteration += 1
                    configuration = Configuration(
                        input_file, 
                        register_scrumbling, 
                        constant_obfuscation, 
                        obfuscation_chain_length, 
                        garbage_blocks, 
                        garbage_length,
                        iteration
                    )
                    thread_pool.apply_async(
                        configuration.evaluate,
                        args = (),
                        callback = save_if_best
                    )

                    if garbage_blocks == 0: break
            if constant_obfuscation == 0: break


    thread_pool.close()
    thread_pool.join()

    print()
    print("DONE")
    print("-" * 40)
    print("Best parameters:")
    print("Register scrambling:", best.register_scrumbling)
    print("Constant obfuscation:", best.constant_obfuscation)
    print("Obfuscation chain length:", best.obfuscation_chain_length)
    print("Garbage blocks:", best.garbage_blocks)
    print("Garbage length:", best.garbage_length)
    print()
    print("Original mean heat:", original_configuration.mean_heat)
    print(f"Best mean heat: {best.mean_heat} ({best.mean_heat / original_configuration.mean_heat * 100:.3f} %)")
    print(f"Overhead introduced: {best.lines_num - original_configuration.lines_num} ({(best.lines_num - original_configuration.lines_num) / original_configuration.lines_num * 100:.3f} %)")
    print("-" * 40)

    # Save best run
    best.id = "best"
    best.evaluate()


if __name__ == "__main__":
    main()