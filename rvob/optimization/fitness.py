import re
from rvob.optimization.ga_structures import population


def punt_heat_3(p: population, id: int, heat_list_after, heat_list_before):
    lenght = len(heat_list_after)
    points = (10000/int(lenght))/32
    ideal_heat = p.individuals[id].heat
    punt = 0
    diff_list = []
    for i in heat_list_after:
        diff_heat = []
        first = True
        for s in range(33):
            if first:
                first = False
            else:
                diff_heat.append(int(i[s] - heat_list_before[s-1]))
        diff_list.append(diff_heat)
    for i in diff_list:
        for s in range(32):
            punt = punt + int(i[s] * points / ideal_heat)
    p.individuals[id].set_punt_heat(punt)


def punt_heat_2(p: population, id: int, heat_list):
    lenght = len(heat_list)
    points = (10000/int(lenght))/32
    ideal_heat = p.individuals[id].heat
    punt = 0
    for i in heat_list:
        first = True
        for s in i:
            if first:
                first = False
            else:
                if s >= ideal_heat / 2:
                    diff = int(s) - ideal_heat / 2
                    punt = punt + int((diff * points) / ideal_heat / 2)
                else:
                    diff = ideal_heat / 2 - int(s)
                    punt = punt + int(((diff * points) / ideal_heat / 2) * -1)
                p.individuals[id].set_punt_heat(punt)
                punt = 0


def punt_heat(p: population, id: int, heat_after, heat_before):
    ideal_heat = p.individuals[id].heat
    punt = 0
    diff_heat = []
    for i in range(len(heat_after)):
        diff_heat.append(int(heat_after[i]-heat_before[i]))
    for i in diff_heat:
        punt = punt + int(i*150/ideal_heat)
        # if i >= ideal_heat/2:
        #    diff = int(i) - ideal_heat/2
        #    punt = punt + int((diff * 312) / ideal_heat/2)
        # else:
        #    diff = ideal_heat/2 - int(i)
        #    punt = punt + int(((diff * 312) / ideal_heat/2) * -1)
    p.individuals[id].set_punt_heat(punt)


def punt_over(p: population, overhead: int, ideal_overhead: int, id: int):
    if overhead <= ideal_overhead:
        diff = ideal_overhead-overhead
        punt = int((diff*10000)/ideal_overhead)
    else:
        if overhead > (2*ideal_overhead):
            punt = -10000
        else:
            diff = overhead - ideal_overhead
            punt = int(((diff * 10000) / ideal_overhead) * -1)
    p.individuals[id].set_punt_over(punt)


def fitness(p: population, id: int, input: str, input2: str, input3: str, id_overhead: int, lenght_file_before: int):

    lenght_before = 0
    lenght_after = 0
    heat_before = 0
    heat_after = 0
    raw_heat_before = []
    raw_heat_after = []
    heat_line = 0

    data = open(input, "r")
    metrics = open(input2, "r")
    num_lines = sum(1 for line in open(input3))

    # recover data from metrics file for the point calc
    for i in metrics:
        if "Mean heat before:" in i:
            heat_before = [int(s) for s in re.findall(r'\b\d+\b', i)]
        if "Executed instructions before:" in i:
            lenght_before = [int(s) for s in re.findall(r'\b\d+\b', i)]
        if "Mean heat after:" in i:
            heat_after = [int(s) for s in re.findall(r'\b\d+\b', i)]
        if "Executed instructions after:" in i:
            lenght_after = [int(s) for s in re.findall(r'\b\d+\b', i)]

    # recover heat from raw data file every 31 instruction
    count = 1
    before = True
    for i in data:
        if count == 0:
            count = 31
            if before:
                heat_line = [int(s) for s in re.findall(r'\b\d+\b', i)]
                raw_heat_before.append(heat_line)
            else:
                heat_line = [int(s) for s in re.findall(r'\b\d+\b', i)]
                raw_heat_after.append(heat_line)
        if "Obfuscated version:" in i:
            before = False
            count = 0
        else:
            count = count - 1
        heat_line = 0

    # closing metrics data file
    data.close()
    metrics.close()

    # calc the metrics for the point assignation
    overhead = int(((num_lines-lenght_file_before)/lenght_file_before)*100)
    punt_over(p, overhead, id_overhead, id)
    # punt_heat(p, id, heat_after, heat_before)
    # punt_heat_2(p, id, raw_heat_after)
    punt_heat_3(p, id, raw_heat_after, heat_before)
