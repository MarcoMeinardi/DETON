import argparse
from os import path
import re
from ast import literal_eval
from deton import execute
from multiprocessing import Pool

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
        "Threads",
        metavar="Number of thread to use",
        help="The number of max thread wanted to be used",
        nargs='?',
        default='1',
        type=int)

    return parser.parse_args()

def run_evaluate(input_file, original_lines_num, register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length, chain_length, iteration, total_iterations):
    mean_heat, lines_num = evaluate(input_file, register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length, chain_length)
    print(input_file)
    print(f"Executed with: {register_scrumbling} {constant_obfuscation} {garbage_blocks} {garbage_length} ({iteration} / {total_iterations})")
    print("New mean heat:", mean_heat)
    print("Overhead introduced:", lines_num - original_lines_num)
    print()
    return mean_heat, lines_num, (register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length, chain_length)

best = None
def save_if_best(values):
    global best
    mean_heat, lines_num, (register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length ,chain_length) = values
    if best is None or mean_heat > best[0]:
        best = (mean_heat, lines_num - original_lines_num, (register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length, chain_length))
    

def evaluate(input_file, register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length, chain_length):
    execute(
        input_file, "", 50, 
        register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length,
        path.dirname(__file__) + '/metrics/output.s', False, True, "tmp", chain_length
    )
    with open(path.dirname(__file__) + '/metrics/data_metricstmp.txt') as f:
        data = f.read()
    mean_heats = literal_eval(re.search(r"Mean heat after: (\[.*\])", data).group(1))
    mean_heat = sum(mean_heats) / 32

    with open(path.dirname(__file__) + '/metrics/output.s') as f:
        lines_num = f.read().count("\n")
    return mean_heat, lines_num


def main():
    global original_lines_num
    args = get_args()
    input_file = args.File
    threads = args.Threads

    original_value, original_lines_num = evaluate(input_file, 0, 0, 0, 0, 0)
    max_overhead = args.Overhead * original_lines_num // 100
    print("Max absolute overhead:", max_overhead)
    print("Original mean heat:", original_value)
    print()

    # Calculate totoa iterations
    total_iterations = 0
    for constant_obfuscation in range(0, max_overhead):
        if constant_obfuscation > max_overhead:
            break
        if constant_obfuscation > 0:
            for chain_length in range(1, 20):
                if constant_obfuscation * chain_length > max_overhead:
                    break
                for garbage_blocks in range(0, max_overhead):
                    if garbage_blocks > 0:
                        if constant_obfuscation * chain_length + garbage_blocks > max_overhead:
                            break
                        for garbage_length in range(1, max_overhead):
                            if constant_obfuscation * chain_length + garbage_blocks * garbage_length > max_overhead:
                                break
                            total_iterations += 1
                    else:
                        total_iterations += 1
        else:
            for garbage_blocks in range(0, max_overhead):
                if garbage_blocks > 0:
                    if garbage_blocks > max_overhead:
                        break
                    for garbage_length in range(1, max_overhead):
                        if garbage_blocks * garbage_length > max_overhead:
                            break
                        total_iterations += 1
                else:
                    total_iterations += 1


    # Try every combination
    iteration = 0
    thread_pool = Pool(threads)
    for constant_obfuscation in range(0, max_overhead):
        if constant_obfuscation > max_overhead:
            break

        if constant_obfuscation > 0:
            for chain_length in range(1, 20):
                if constant_obfuscation * chain_length > max_overhead:
                    break

                for garbage_blocks in range(0, max_overhead):
                    if garbage_blocks > 0:
                        if constant_obfuscation * chain_length + garbage_blocks > max_overhead:
                            break

                        for garbage_length in range(1, max_overhead):
                            if constant_obfuscation * chain_length + garbage_blocks * garbage_length > max_overhead:
                                break

                            register_scrumbling = max_overhead - constant_obfuscation * chain_length - garbage_blocks * garbage_length
                            iteration += 1
                            thread_pool.apply_async(
                                run_evaluate,
                                args = (input_file, original_lines_num, register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length, chain_length, iteration, total_iterations),
                                callback = save_if_best
                            )

                    else:
                        register_scrumbling = max_overhead - constant_obfuscation * chain_length
                        iteration += 1
                        thread_pool.apply_async(
                            run_evaluate,
                            args = (input_file, original_lines_num, register_scrumbling, constant_obfuscation, 0, 0, chain_length, iteration, total_iterations),
                            callback = save_if_best
                        )
        
        else:
            for garbage_blocks in range(0, max_overhead):
                if garbage_blocks > 0:
                    if garbage_blocks > max_overhead:
                        break

                    for garbage_length in range(1, max_overhead):
                        if garbage_blocks * garbage_length > max_overhead:
                            break

                        register_scrumbling = max_overhead - garbage_blocks * garbage_length
                        iteration += 1
                        thread_pool.apply_async(
                            run_evaluate,
                            args = (input_file, original_lines_num, register_scrumbling, constant_obfuscation, garbage_blocks, garbage_length, 0, iteration, total_iterations),
                            callback = save_if_best
                        )

                else:
                    register_scrumbling = max_overhead
                    iteration += 1
                    thread_pool.apply_async(
                        run_evaluate,
                        args = (input_file, original_lines_num, register_scrumbling, constant_obfuscation, 0, 0, 0, iteration, total_iterations),
                        callback = save_if_best
                    )


    thread_pool.close()
    thread_pool.join()

    print()
    print("DONE")
    print("Best parameters:")
    print("Register scrambling:", best[2][0])
    print("Constant obfuscation:", best[2][1])
    print("Garbage blocks:", best[2][2])
    print("Garbage length:", best[2][3])
    print("Chain length:", best[2][4])
    print()
    print("Original mean heat:", original_value)
    print("Best mean heat:", best[0])
    print("Overhead introduced:", best[1])

    execute(
        input_file, "", 50, 
        best[2][0], best[2][1], best[2][2], best[2][3],
        path.dirname(__file__) + '/metrics/output.s', False, True, "best",
        best[2][4]
    )



if __name__ == "__main__":
    main()