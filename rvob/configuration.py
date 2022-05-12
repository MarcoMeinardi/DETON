from deton import execute
from os import path
from ast import literal_eval
import re

class Configuration:
    def __init__(self, input_data, register_scrumbling, constant_obfuscation, obfuscation_chain_length, garbage_blocks, garbage_length, id):
        self.input_data = input_data
        self.register_scrumbling = register_scrumbling
        self.constant_obfuscation = constant_obfuscation
        self.obfuscation_chain_length = obfuscation_chain_length
        self.garbage_blocks = garbage_blocks
        self.garbage_length = garbage_length
        self.id = id

    def get_parameters(self):
        return (
            self.input_data, 
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
            self.input_data[0], self.input_data[1], 50, 
            self.register_scrumbling, self.constant_obfuscation, self.obfuscation_chain_length, self.garbage_blocks, self.garbage_length,
            path.dirname(__file__) + f"/metrics/output_{output_name}.s", False, True, f"_{output_name}"
        )
        with open(path.dirname(__file__) + f"/metrics/data_metrics_{output_name}.txt") as f:
            data = f.read()
            
        mean_heats = tuple(literal_eval(re.search(r"Mean heat after: (\[.*\])", data).group(1)))
        self.mean_heat = sum(mean_heats) / len(mean_heats)
        self.mean_heats = mean_heats

        with open(path.dirname(__file__) + f"/metrics/output_{output_name}.s") as f:
            self.lines_num = f.read().count("\n")

        return self

    def __str__(self):
        return f"{self.register_scrumbling} {self.constant_obfuscation} {self.obfuscation_chain_length} {self.garbage_blocks} {self.garbage_length}"
