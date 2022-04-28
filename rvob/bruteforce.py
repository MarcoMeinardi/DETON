import argparse
from os import path
import re
from ast import literal_eval
from deton import execute

def get_args():
    parser = argparse.ArgumentParser(description="Bruteforce of DETON")

    parser.add_argument(
        "Overhead",
        metavar="max overhead value",
        help="The maximum Overhead value wanted in % compared to the original file",
        default='50',
        type=int)

    parser.add_argument(
        "File",
        metavar="File path input",
        help="The path of the file in .json format to process",
        nargs='?',
        default='q',
        type=str)

    parser.add_argument(
        '-s', '-stats',
        help="Print stats and plot",
        nargs='?',
        default=False,
        type=bool)

    return parser.parse_args()

def evaluate(input_file, register_scrumbling, costant_obfuscation, garbage_blocks, garbage_length):
    mean_mean_heat = 0 # randomness is though
    for i in range(3):
        execute(
            input_file, "", 50, 
            register_scrumbling, costant_obfuscation, garbage_blocks, garbage_length,
            path.dirname(__file__) + '/metrics/output.s', False, True
        )
        with open(path.dirname(__file__) + '/metrics/data_metrics1.txt') as f:
            data = f.read()
        mean_heats = literal_eval(re.search(r"Mean heat after: (\[.*\])", data).group(1))
        mean_heat = sum(mean_heats) / 32
        mean_mean_heat += mean_heat / 3
    return mean_mean_heat


def main():
    args = get_args()
    input_file = args.File
    max_overhead = args.Overhead

    original_value = evaluate(input_file, 0, 0, 0, 0)
    
    print("Original mean heat:", original_value)
    print()

    costant_chain_length = 8

    total_iterations = 0
    for costant_obfuscation in range(0, max_overhead):
        if costant_obfuscation * costant_chain_length > max_overhead:
            break
        for garbage_blocks in range(0, max_overhead):
            if garbage_blocks > 0:
                if costant_obfuscation * costant_chain_length + garbage_blocks > max_overhead:
                    break
                for garbage_length in range(1, max_overhead):
                    if costant_obfuscation * costant_chain_length + garbage_blocks * garbage_length > max_overhead:
                        break
                    total_iterations += 1
            else:
                total_iterations += 1

    best = (original_value, (0, 0, 0, 0))
    iteration = 0
    for costant_obfuscation in range(0, max_overhead):
        if costant_obfuscation * costant_chain_length > max_overhead:
            break

        for garbage_blocks in range(0, max_overhead):
            if garbage_blocks > 0:
                if costant_obfuscation * costant_chain_length + garbage_blocks > max_overhead:
                    break

                for garbage_length in range(1, max_overhead):
                    if costant_obfuscation * costant_chain_length + garbage_blocks * garbage_length > max_overhead:
                        break

                    register_scrumbling = max_overhead - costant_obfuscation * costant_chain_length - garbage_blocks * garbage_length
                    iteration += 1
                    print(f"Executing with: {register_scrumbling} {costant_obfuscation} {garbage_blocks} {garbage_length} ({iteration} / {total_iterations})")
                    
                    new_value = evaluate(input_file, register_scrumbling, costant_obfuscation, garbage_blocks, garbage_length)
                    
                    print("New mean heat:", new_value)
                    if new_value > best[0]:
                        best = (new_value, (register_scrumbling, costant_obfuscation, garbage_blocks, garbage_length))



            else:
                register_scrumbling = max_overhead - costant_obfuscation * costant_chain_length
                iteration += 1
                print(f"Executing with: {register_scrumbling} {costant_obfuscation} {0} {0} ({iteration} / {total_iterations})")
                
                new_value = evaluate(input_file, register_scrumbling, costant_obfuscation, 0, 0)
                
                print("New mean heat:", new_value)
                if new_value > best[0]:
                    best = (new_value, (register_scrumbling, costant_obfuscation, 0, 0))
 
    print()
    print("DONE")
    print("Best parameters:")
    print("Register scrambling:", best[1][0])
    print("Costant obfuscation:", best[1][1])
    print("Garbage blocks:", best[1][2])
    print("Garbage length:", best[1][3])
    print()
    print("Original mean heat:", original_value)
    print("Best mean heat:", best[0])

    execute(
        input_file, "", 50, 
        *best[1],
        path.dirname(__file__) + '/metrics/output.s', False, True, "best"
    )



if __name__ == "__main__":
    main()