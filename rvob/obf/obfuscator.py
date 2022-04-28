from random import seed, randint, sample, choice
from typing import List, Tuple
from obf.const_derivation import generate_derivation_chain, Promise, primers
from rep.base import Instruction, to_line_iterator, Statement
from rvob.registerbinder import bind_register_to_value
from structures import Register, opcd_family, not_modifiable_regs
from networkx import DiGraph
from queue import Queue


class NotEnoughRegisters(Exception):
    pass


class NotValidInstruction(Exception):
    pass


class NodeBlock:
    """
    A utility object that contains all the data that are relevant for the process of choosing where to put the
    instructions in a node
    @var node_id: the id of the node represented by the block
    @var init_line: the first line where you can insert an instruction
    @var end_line: the last line where you can insert an instruction
    """

    def __init__(self, node_id: int, reg_pool: set, init_line: int, end_line: int):
        self.node_id = node_id
        self.reg_pool = reg_pool
        self.init_line = init_line
        self.end_line = end_line
        self.conjunction_reg = None

    node_id: int
    reg_pool: set
    init_line: int
    end_line: int
    conjunction_reg: Register


def evaluate_next_node(cfg: DiGraph, actual_node: int, register) -> NodeBlock:
    """
    the function test if the next node is a valid one where to put part of the new instruction generated by the constant
    obfuscation. To be valid a node must have no more than 1 successors and 1 predecessors, must have at least 1 usable
    register
    @param cfg: the graph representing the program
    @param actual_node: the current node already analyzed
    @param register: the used by the original instruction, it must not be used by the first instruction of the next node
    @return: a NodeBlock corresponding to the next node if it's a valid one, otherwise None will be returned
    """
    successors = list(node for node in cfg.successors(actual_node))
    predecessors = list(node for node in cfg.predecessors(actual_node))
    if (len(successors) >= 2) or (len(predecessors) >= 2) or ('external' in cfg.nodes[successors[0]]):
        return None
    else:
        actual_node = successors[0]
        actual_block = cfg.nodes[actual_node]["block"]
        reg_pool = calc_free_reg(cfg.nodes[actual_node])
        node_block = NodeBlock(actual_node, reg_pool, actual_block.begin, actual_block.begin)
        first_line = actual_block[node_block.init_line]
        if len(first_line.labels) != 0:
            if (first_line.r2 == register) or (first_line.r3 == register):
                return None
            else:
                node_block.init_line += 1
                node_block.end_line += 1
        if len(reg_pool) <= 1:
            return None
        return node_block


def calc_free_reg(node: DiGraph.node, start_line: int = None) -> set:
    """
    The function calculates which are the usable registers in a given node of the graph, the obtained set is calculated
    by removing from set set of all the register the "not modifiable register" and the register contained in the "reg_bind"
    attribute of the node
    @param node: the node we need the free register
    @param start_line: initial line of the alternative sequence (if this is the first node)
    @return: the set of the usable register for the current node
    """

    free_reg = set(Register.list())
    free_reg -= not_modifiable_regs
    if start_line is not None:
        used = []
        for reg in node["reg_bind"].keys():
            for block in node["reg_bind"][reg]:
                if block.init_line >= start_line or block.end_line >= start_line:
                    used.append(reg)
        free_reg -= set(used)
    else:
        free_reg -= set(reg for reg in node["reg_bind"].keys())
    return free_reg


def is_store_instruction(instr: Instruction) -> bool:
    """
    check if instr is a store instruction, in this case the first register is read
    @param instr: instruction to be checked
    @return: true if instr is a store instruction
    """
    if instr.opcode == "sw" or instr.opcode == "sh" or instr.opcode == "sb":
        return True
    else:
        return False


def calc_nodes_chain(cfg: DiGraph, start_node: int, start_line: int, register: Register) -> List[NodeBlock]:
    """
    This function search for all the valid node in which an instruction ca be added. The valid node are those that
    doesn't have sibling nodes. A node is valid until the line in which the rd register of the non-obfuscated
    instruction is used
    @param cfg: the graph that represents the assembly program
    @param start_node: the node where is present the instruction that will be obfuscated
    @param start_line: the line of the instruction that will be obfuscated
    @param register: the destination register used by the instruction that will be obfuscated
    @return: a list of NodeBlock
    """
    actual_node = start_node
    actual_block = cfg.nodes[actual_node]["block"]
    node_chain = [NodeBlock(start_node, calc_free_reg(cfg.nodes[start_node], start_line), start_line, start_line)]
    if len(node_chain[0].reg_pool) <= 1:
        raise NotEnoughRegisters
    if start_line == (cfg.nodes[start_node]['block'].end - 1):
        next_node = evaluate_next_node(cfg, actual_node, register)
        if next_node is None:
            return node_chain
        else:
            conjunction = sample(node_chain[-1].reg_pool.intersection(next_node.reg_pool), 1)[0]
            if conjunction is None or len(node_chain[-1].reg_pool) <= 2:
                return node_chain
            else:
                node_chain[-1].conjunction_reg = conjunction
                node_chain[-1].reg_pool.remove(conjunction)
                next_node.reg_pool.remove(conjunction)
                node_chain.append(next_node)
                actual_node = next_node.node_id
                actual_block = cfg.nodes[next_node.node_id]['block']
                line = next_node.init_line
    else:
        line = start_line
    while True:
        for instr in actual_block.iter(line):
            if (instr.r2 == register) or (instr.r3 == register) or (
                    is_store_instruction(instr) and instr.r1 == register):
                return node_chain
            node_chain[-1].end_line += 1
        next_node = evaluate_next_node(cfg, actual_node, register)
        if next_node is None:
            return node_chain
        else:
            conjunction = sample(node_chain[-1].reg_pool.intersection(next_node.reg_pool), 1)[0]
            if conjunction is None or len(node_chain[-1].reg_pool) <= 2:
                return node_chain
            else:
                node_chain[-1].conjunction_reg = conjunction
                node_chain[-1].reg_pool.remove(conjunction)
                next_node.reg_pool.remove(conjunction)
                node_chain.append(next_node)
                line = next_node.init_line
                actual_node = next_node.node_id
                actual_block = cfg.nodes[next_node.node_id]['block']


# def calc_unresolved_register(prm_chain: List[Promise]) -> int:
#     """
#     This function calculates the number of unresolved registers
#     @param prm_chain: a list of promises
#     @return: the number of needed free registers
#     """
#     virtual_reg = set()
#     for promise in prm_chain:
#         if isinstance(promise.rd, int):
#             virtual_reg.add(promise.rd)
#         if isinstance(promise.rs1, int):
#             virtual_reg.add(promise.rs1)
#         if isinstance(promise.rs2, int):
#             virtual_reg.add(promise.rs2)
#     return len(virtual_reg)


def generate_positions(node_chain: List[NodeBlock], obj_num: int) -> List[Tuple[int, List[int]]]:
    """
    the function select randomly the positions in which insert the instructions that is the obfuscated version of a
    previously chosen instruction
    @param node_chain: the list of NodeBlock that identify the valid nodes where to put the new instruction generated by
                        the constant obfuscation
    @param obj_num: the number of the instructions that will substitute the non-obfuscated one
    @return: a list of tuples of the type: (node_id, list of lines in which insert the instructions)
    """
    seed()
    positions = list()
    # redistribute the promises over the selected nodes
    a = sample(range(0, obj_num), len(node_chain) - 1) + [0, obj_num]
    list.sort(a)
    b = [a[i + 1] - a[i] for i in range(len(a) - 1)]
    for i in range(len(b)):
        node = node_chain[i].node_id
        pos = list()
        available_line = (node_chain[i].end_line - node_chain[i].init_line)
        if available_line >= b[i]:
            pos = sample(range(node_chain[i].init_line, node_chain[i].end_line), b[i])
            pos.sort()
        else:
            for x in range(b[i]):
                pos.append(node_chain[i].init_line + x)
        positions.append((node, pos))
    shift_amount = [0 for _ in range(len(positions))]
    for t in range(len(positions)):
        for t2 in range(0, t):
            if t != t2 and len(positions[t2][1]) > 0 and len(positions[t][1]) > 0 and positions[t2][1][0] < \
                    positions[t][1][0]:
                shift_amount[t] += len(positions[t2][1])
    for t in range(len(positions)):
        for t2 in range(len(positions[t][1])):
            positions[t][1][t2] += shift_amount[t]
    return positions


def check_reg(virtual_reg, matrix, selected_reg: Register) -> str:
    """
    check if a register, that is contained in a promise, is clearly defined or is associated to a number that act as
    a pseudo-name; in this last case the function try to check if that pseudo-name is already solved to a real register
    otherwise chose randomly a free reg to associate to it
    @param virtual_reg: the register to inspect
    @param matrix: the dictionary that contains all the association between pseudo-name and register already solved
    @param selected_reg: the register to use, in case virtual_reg is a placeholder and there isn't a match in
                        the register matrix
    @return: the name of a real register
    """
    if isinstance(virtual_reg, int):
        try:
            reg = matrix[virtual_reg]
        except KeyError:
            matrix[virtual_reg] = selected_reg
            reg = selected_reg
        return reg
    else:
        return virtual_reg


def fix_original_instruction(line: int, new_instr: List[Tuple[int, List[int]]]):
    """
    adjust the line number of the instruction that will be obfuscated taking into account the positions of the newly
    added instructions
    @param line: the original line number of the instruction to be obfusctaed
    @param new_instr: the list of the positions of the new instructions
    @return: the adjusted value of the line number of the original instruction
    """
    for i in range(len(new_instr)):
        for t in range(len(new_instr[i][1])):
            if new_instr[i][1][t] <= line:
                line += 1
    return line


def placer(cfg: DiGraph, promises: List[Promise], node_chain: List[NodeBlock], target_instr: int) -> int:
    """
    the role of this function is to convert the promises into real instructions and insert these one in the previously
    identified positions
    @param node_chain: the list of NodeBlock that identify the valid nodes where to put the new instruction generated by
                       the constant obfuscation
    @param target_instr: the instruction to be obfuscated
    @param cfg: the graph that represent the assembly program
    @param promises: the list of promises
    """
    register_matrix = {}
    positions = generate_positions(node_chain, len(promises))
    iter_list = list()
    for i in range(len(positions)):
        for t in range(len(positions[i][1])):
            iter_list.append(i)
    target_instr = fix_original_instruction(target_instr, positions)
    instr_queue = Queue()
    promises.reverse()
    next_pos = 1
    for prom, i in zip(promises, iter_list):
        if i != iter_list[next_pos]:
            rd = check_reg(prom.rd, register_matrix, node_chain[i].conjunction_reg)
        else:
            rd = check_reg(prom.rd, register_matrix, sample(node_chain[i].reg_pool, 1)[0])
        rs1 = check_reg(prom.rs1, register_matrix, sample(node_chain[i].reg_pool, 1)[0])
        rs2 = check_reg(prom.rs2, register_matrix, sample(node_chain[i].reg_pool, 1)[0])
        instr = Instruction(prom.op.name.lower(), opcd_family[prom.op.name.lower()], r1=rd, r2=rs1, r3=rs2,
                            immediate=prom.const)
        instr.inserted = True
        instr_queue.put(instr)
        if next_pos < len(iter_list)-1:
            next_pos += 1
    for i in range(len(positions)):
        active_block = cfg.nodes[positions[i][0]]['block']
        for t in range(len(positions[i][1])):
            line = positions[i][1][t]
            instr = instr_queue.get()
            active_block.insert(line, instr)
            bind_register_to_value(cfg, positions[i][0])
    return target_instr


def get_immediate_instructions(cfg) -> Tuple[int, int]:
    """
    The functions search for all the immediate instructions in the specified cfg and
    returns a tuple where the first parameter represents a node and the second one is a line number.
    :param cfg:
    :return: (node, line_num)
    """
    result = []
    for node in cfg.nodes:
        if "external" not in cfg.nodes[node]:
            current_node = cfg.nodes[node]
            iterator = to_line_iterator(current_node['block'].iter(current_node['block'].begin),
                                        current_node['block'].begin)
            while True:
                try:
                    line = iterator.__next__()
                    line_num = line.number
                    if isinstance(line.statement, Instruction):
                        stat: Instruction = line.statement
                        if (stat.opcode in primers or stat.opcode == "li") and stat.immediate is not None \
                                and stat.immediate.symbol is None:
                            result.append((node, line_num))
                except StopIteration:
                    break
    if len(result) == 0:
        raise NotValidInstruction
    return choice(result)


def obfuscate(cfg: DiGraph, node_id: int = None, target_instr: int = None):
    """
    this is the main function that, given an instruction, generate the list of promises, convert them into instructions
    and distribute them in as many nodes as possible
    @param cfg: the graph that represent the assembly program
    @param node_id: the id of the node where is collocated the instruction to obfuscate
    @param target_instr: the line of the instruction to obfuscate
    """
    seed()
    if node_id is None or target_instr is None:
        extracted = get_immediate_instructions(cfg)
        node_id = extracted[0]
        target_instr = extracted[1]
    instruction = cfg.nodes[node_id]["block"][target_instr]
    max_shift = 3
    max_logical = 5
    promise_chain = generate_derivation_chain(instruction, max_shift, max_logical)
    node_chain = calc_nodes_chain(cfg, node_id, target_instr, instruction.r1)
    target_instr_off = placer(cfg, promise_chain, node_chain, target_instr)
    if len(instruction.labels) > 0:
        succ_instr = cfg.nodes[node_id]['block'][target_instr]
        succ_instr.labels = instruction.labels
    del cfg.nodes[node_id]['block'][target_instr_off]
