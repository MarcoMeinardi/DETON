from collections import deque
from enum import Enum
from itertools import count, chain
from typing import Iterator, FrozenSet, List, Tuple, Optional, Mapping, Hashable, Iterable, MutableMapping, NamedTuple

from networkx import DiGraph, simple_cycles, restricted_view, all_simple_paths

from rep.base import Instruction, Directive, ASMLine, to_line_iterator
from rep.fragments import Source, FragmentView, CodeFragment


class InvalidCodeError(Exception):
    """An error raised when a code fragment doesn't follow some expected layout or assumption."""

    pass


class Transition(Enum):
    """
    A type of control flow progression.

    Each member carries some information characterizing the type of advancement:

    - resolve_symbol: whether the progression implies a symbol resolution;
    - branching: whether progressing in this direction is conditional.
    """

    SEQ = (False, False)
    """Sequential advancement: PC advances linearly, towards the instruction that follows."""

    U_JUMP = (True, False)
    """Unconditional jump: a simple local unconditional jump."""

    C_JUMP = (True, True)
    """ Conditional jump: a simple local conditional jump. An alternate sequential execution path exists."""

    CALL = (True, False)
    """Procedure call: non-local jump to an internal or external procedure."""

    RETURN = (False, False)
    """Return: return jump from a call."""

    def __new__(cls, *args, **kwargs):
        # Calculate a unique ID to avoid aliasing
        id_val = len(cls.__members__) + 1
        instance = object.__new__(cls)
        instance._value_ = id_val
        return instance

    def __init__(self, resolve_symbol: bool, branching: bool):
        self.resolve_symbol = resolve_symbol
        self.branching = branching

    def __repr__(self):
        return '<%s.%s: (%s,%s)>' % (self.__class__.__name__, self.name, self.resolve_symbol, self.branching)


jump_ops: Mapping[str, Transition] = {
    "call": Transition.CALL,
    "jr": Transition.RETURN,
    "j": Transition.U_JUMP,
    "jal": Transition.CALL,
    "jalr": Transition.CALL,
    "beq": Transition.C_JUMP,
    "beqz": Transition.C_JUMP,
    "bne": Transition.C_JUMP,
    "bnez": Transition.C_JUMP,
    "blt": Transition.C_JUMP,
    "bltz": Transition.C_JUMP,
    "bltu": Transition.C_JUMP,
    "ble": Transition.C_JUMP,
    "blez": Transition.C_JUMP,
    "bleu": Transition.C_JUMP,
    "bgt": Transition.C_JUMP,
    "bgtz": Transition.C_JUMP,
    "bgtu": Transition.C_JUMP,
    "bge": Transition.C_JUMP,
    "bgez": Transition.C_JUMP,
    "bgeu": Transition.C_JUMP
}
"""Mapping between control flow manipulation instructions and the kind of transition that they introduce."""


class BasicBlock:
    """
    A program's basic block.

    Each member of this class is a code container, decorated with additional metadata that would have to be extracted
    every time from bare assembly.

    Members of this class are identified by some hashable object. Uniqueness is not enforced.

    :ivar identifier: the hashable identifier for the basic block
    :ivar labels: labels representing marking the entry point for the basic block, if any
    :ivar code: the code fragment containing the actual code
    :ivar outgoing_flow: the shape of the outgoing flow and its destination, in the format returned by the
          execution_flow_at function
    """

    identifier: Hashable
    labels: List[str]
    code: CodeFragment
    outgoing_flow: Tuple[Transition, Optional[str]]

    def __init__(self, fragment: CodeFragment, block_id: Hashable):
        starting_line = fragment[fragment.begin]
        ending_line = fragment[fragment.end - 1]

        if not isinstance(ending_line, Instruction):
            raise InvalidCodeError("A basic block must always end with an instruction.")

        self.identifier = block_id
        self.labels = list(starting_line.labels)
        self.code = fragment
        self.outgoing_flow = execution_flow_at(ending_line)

    def __repr__(self):
        return "BasicBlock(" + repr(self.code) + ", " + repr(self.identifier) + ")"

    def __str__(self):
        return "---\nBB ID: " + str(self.identifier) + "\nLabels: " + str(self.labels) + "\n\n" + str(self.code) + \
               "\nOutgoing exec arc: " + str(self.outgoing_flow) + "\n---\n"


class ProcedureCall(NamedTuple):
    """
    A procedure call.

    Calls are represented in terms of caller, callee and point where execution is expected to return
    (`confluence point`).
    """

    caller: Hashable
    callee: Hashable
    confluence_point: Hashable


class LocalGraph:
    """
    A CFG representing some part of a program, with unresolved procedure calls.

    A local graph is characterized by an entry-point, a digraph, some terminal nodes and a collection of "arcs"
    directed to some external procedures. There is only one execution flow that traverses a local graph, starting from
    the entry-point and eventually branching until the terminal nodes are reached, unless an external call diverges.

    A local graph may not be connected, with disconnected components being confluence point for flows returning from
    external calls. The information necessary to extract a connected graph can be extracted by resolving the external
    calls.

    No check is performed on the consistency of the information used to instantiate these objects.
    """

    entry_labels: List[str]
    entry_point_id: Hashable
    graph: DiGraph
    external_calls: List[ProcedureCall]
    terminal_nodes_ids: List[Hashable]

    def __init__(self,
                 entry_point: Hashable,
                 graph: DiGraph,
                 calls: Iterable[ProcedureCall],
                 terminals: Iterable[Hashable]):
        """
        Construct a new local graph.

        :param entry_point: the entry-point's ID
        :param graph: the local graph, as a NetworkX DiGraph
        :param calls: a collection of purportedly external calls
        :param terminals: a collection of node IDs indicating which are the termianl nodes
        """
        leading_block = graph.nodes[entry_point]

        # Set up the entry-point information
        self.entry_point_id = entry_point
        self.entry_labels = leading_block['labels']

        # Characterize the function in terms of a graph and the nested calls it performs
        self.graph = graph
        self.external_calls = list(calls)

        # Keep track of the terminal nodes
        self.terminal_nodes_ids = list(terminals)


def execution_flow_at(inst: Instruction) -> Tuple[Transition, Optional[str]]:
    """
    Determine the state of the execution flow at the given instruction.

    This function returns a tuple containing a `Transition` type specifier and, in case of a jump, the symbol
    representing its destination. The transition type indicates in what manner the execution flow shall progress past
    the given instruction.

    :param inst: the instruction at which the control flow status must be checked
    :return: the tuple containing the parting transition
    """

    if inst.opcode in jump_ops:
        trans_type = jump_ops[inst.opcode]
        if trans_type.resolve_symbol:
            return trans_type, inst.immediate.symbol
        else:
            return trans_type, None
    else:
        # Any instruction that is not a jump instruction must maintain the sequential control flow
        return Transition.SEQ, None


def basic_blocks(code: CodeFragment) -> List[BasicBlock]:
    """
    Extract the basic blocks from a code fragment.

    The resulting basic blocks contain views on the source fragment, and come in the same order in which they appear in
    the original fragment. Non-code statements are discarded if they reside between BB boundaries and are not
    interleaved with code statements.

    For a correct behaviour, launch this function on a well-delimited code fragment (started by at least one label,
    terminated by a jump).

    Be aware that fancy ways of jumping around based on runtime-loaded addresses are not currently supported by this
    package.

    :param code: the code fragment whose basic blocks will be extracted
    :return: the list of basic blocks contained in the original fragment
    :raise InvalidCodeError: when the provided code fragment has no label or no outgoing jump
    """

    # Identify the block boundaries, that is: those lines marked by a label or containing a control transfer instruction
    block_boundaries = filter(lambda asl: isinstance(asl.statement, Instruction)
                                          and (asl.statement.opcode in jump_ops or len(asl.statement.labels) > 0),
                              # Use a line-oriented iterator, so that we can extract the line numbers
                              to_line_iterator(iter(code), code.begin))

    # Given the boundaries, calculate the appropriate cutoff points.
    # A dictionary is used as a way of implementing an "ordered set" for easy duplicate removal.
    # TODO find a more elegant way to remove duplicates online
    cutoff_points = dict()
    for boundary in block_boundaries:
        if len(boundary.statement.labels) > 0 and boundary.statement.opcode in jump_ops:
            # For a labeled line that also contains a jump, record two cut-points so that a single-line block can be
            # created.
            cutoff_points[boundary.number] = None
            cutoff_points[boundary.number + 1] = None
        elif len(boundary.statement.labels) > 0:
            # Labeled lines mark cut-points themselves
            cutoff_points[boundary.number] = None
        else:
            # A cut has to be made below any line containing a jump
            cutoff_points[boundary.number + 1] = None

    if len(cutoff_points) < 2:
        raise InvalidCodeError("Code fragment does not start with a label or end with a jump/return.")

    # Convert the "ordered set" back into a list
    cutoff_points = list(iter(cutoff_points))

    # Start slicing code into basic blocks
    bb = []
    head = cutoff_points[0]
    seq = count(1)
    for tail in cutoff_points[1:]:
        if any(isinstance(line, Instruction) for line in code[head:tail]):
            bb.append(BasicBlock(FragmentView(code, head, tail, head), next(seq)))
        head = tail

    return bb


def local_cfg(bbs: List[BasicBlock]) -> LocalGraph:
    """
    Construct a local graph from a list of basic blocks.

    Nodes and edges of the resulting graph will be decorated, respectively, with assembly labels and transition types,
    registered with the attribute names of `labels` and `kind`.

    This function works based on a few assumptions:

    - the basic blocks are provided in the same order they appear inside the original code fragment;
    - the first block is the entry-point;
    - all `call` instructions point to code not contained in the provided basic blocks;
    - all jumps are local;
    - all blocks with a final `RETURN` transition actually return control to whoever caused the PC to reach the EP.
    When these conditions are satisfied, a well-formed local graph is returned.

    :param bbs: the list of basic blocks of which the local graph is formed
    :return: a LocalGraph object representing the local graph
    """

    local_graph = DiGraph()

    local_symbol_table: MutableMapping[str, Hashable] = {}
    pending_jumps: List[Tuple[Hashable, str, Transition]] = []

    terminal_nodes = []
    calls = []

    parent_seq_block = None
    pending_call = None

    for bb in bbs:
        local_graph.add_node(bb.identifier, labels=list(bb.labels), block=bb.code)

        if parent_seq_block is not None:
            # Attach the current node to the sequence-wise previous one
            local_graph.add_edge(parent_seq_block, bb.identifier, kind=Transition.SEQ)
            parent_seq_block = None
        elif pending_call is not None:
            # Set the current node as the return point of a procedure call
            calls.append(ProcedureCall(pending_call[0], pending_call[1], bb.identifier))
            pending_call = None

        # Embed the basic block's labels into the node
        local_symbol_table.update((lab, bb.identifier) for lab in bb.labels)

        outgoing_transition = bb.outgoing_flow[0]
        if outgoing_transition is Transition.RETURN:
            # The outgoing transition is a return-jump: add the node to the list of terminals.
            terminal_nodes.append(bb.identifier)
        elif outgoing_transition is Transition.CALL:
            # The outgoing transition is a procedure call: keep track of it so that the subsequent block will be set as
            # its confluence point.
            pending_call = bb.identifier, bb.outgoing_flow[1]
        else:
            if outgoing_transition is Transition.SEQ or outgoing_transition.branching:
                # In case of a sequential or branching transition, the subsequent basic block is to be attached to the
                # current one.
                parent_seq_block = bb.identifier

            if outgoing_transition.resolve_symbol:
                # In case of a jump, store its origin and symbolic destination for the coming one-pass resolution.
                pending_jumps.append((bb.identifier, bb.outgoing_flow[1], bb.outgoing_flow[0]))

    for jumper, dst, kind in pending_jumps:
        # Resolve the internal symbolic jumps and add the missing edges
        local_graph.add_edge(jumper, local_symbol_table[dst], kind=kind)

    return LocalGraph(bbs[0].identifier, local_graph, calls, terminal_nodes)


def build_cfg(src: Source, entry_point: str = "main") -> DiGraph:
    """
    Builds the CFG of the supplied assembly code, starting from the specified entry point.
    
    The entry point consists of a valid label pointing to what will be considered by the algorithm as the first
    instruction executed by a caller.
    The graph is built through a recursive DFS algorithm that follows the control flow.

    The resulting graph's nodes either contain a reference to a view, through the node attribute `block`, which
    represents the block of serial instructions associated with the node, or an `external` flag, signifying that the
    referenced code is external to the analyzed code.
    Nodes representing internal code have an incremental ID, while the external ones are uniquely identified through
    their symbol (aka procedure identifier).

    Nodes are connected through unweighted edges bearing a `kind` attribute, which describes the type of transition that
    that edge represents.

    :param src: the assembler source to be analyzed
    :param entry_point: the entry point from which the execution flow will be followed
    :return: a directed graph representing the CFG of the analyzed code
    :raise ValueError: when the entry point couldn't be found
    """

    def _explorer(start_line: int, __ret_stack__: deque):
        # Detect if there's a loop and eventually return the ancestor's ID to the caller
        if start_line in ancestors:
            return ancestors[start_line]

        # Instantiate an iterator that scans the source, ignoring directives
        line_supplier = filter(lambda s: isinstance(s.statement, Instruction),
                               to_line_iterator(src.iter(start_line), start_line))
        # Generate node ID for the root of the local subtree
        rid = next(id_sup)

        # Variable for keeping track of the previous line, in case we need to reference it
        previous_line = None

        for line in line_supplier:
            if len(line.statement.labels) != 0 and line.number != start_line:
                # TODO maybe we can make this iterative?
                # We stepped inside a new contiguous block: build the node for the previous block and relay
                cfg.add_node(rid, block=FragmentView(src, start_line, line.number, start_line))
                ancestors[start_line] = rid
                cfg.add_edge(rid, _explorer(line.number, __ret_stack__), kind=Transition.SEQ)
                break
            elif line.statement.opcode in jump_ops:
                # Create node
                cfg.add_node(rid, block=FragmentView(src, start_line, line.number + 1, start_line))
                ancestors[start_line] = rid

                if jump_ops[line.statement.opcode] == Transition.U_JUMP:
                    # Unconditional jump: resolve destination and relay-call explorer there
                    cfg.add_edge(rid,
                                 _explorer(label_dict[line.statement.immediate.symbol], __ret_stack__),
                                 kind=Transition.U_JUMP)
                    break
                elif jump_ops[line.statement.opcode] == Transition.CALL:
                    # Function call: start by resolving destination
                    target = line.statement.immediate.symbol
                    # TODO find a way to modularize things so that this jump resolution can be moved out of its nest
                    try:
                        dst = label_dict[target]
                        # Update the return address
                        ret_stack.append(next(line_supplier).number)
                        # Set the current node as ancestor for the recursive explorer
                        home = rid
                        # Set transition type to CALL
                        tran_type = Transition.CALL
                    except KeyError:
                        # Calling an external function: add an edge to the external code node.
                        # The external node is uniquely identified by a call ID, so that client code of the graph can
                        # follow the execution flow among calls to the same external procedures.
                        call_id = target + str(next(id_sup))
                        cfg.add_node(call_id, external=True)
                        cfg.add_edge(rid, call_id, kind=Transition.CALL)

                        # Set the following line as destination
                        dst = next(line_supplier).number
                        # Set the external node as ancestor for the recursive explorer
                        home = call_id
                        # Set the the type of the transition from the external code back to us as RETURN
                        tran_type = Transition.RETURN

                    # Perform the actual recursive call
                    cfg.add_edge(home, _explorer(dst, __ret_stack__), kind=tran_type)
                    break
                elif jump_ops[line.statement.opcode] == Transition.C_JUMP:
                    # Conditional jump: launch two explorers, one at the jump's target and one at the following line
                    cfg.add_edge(rid, _explorer(next(line_supplier).number, __ret_stack__), kind=Transition.SEQ)
                    # The second explorer needs a copy of the return stack, since it may encounter another return jump
                    cfg.add_edge(rid,
                                 _explorer(label_dict[line.statement.immediate.symbol],
                                           __ret_stack__.copy()),
                                 kind=Transition.C_JUMP)
                    break
                elif jump_ops[line.statement.opcode] == Transition.RETURN:
                    # Procedure return: close the edge on the return address by invoking an explorer there
                    cfg.add_edge(rid, _explorer(__ret_stack__.pop(), __ret_stack__), kind=Transition.RETURN)
                    break
                else:
                    raise LookupError("Unrecognized jump type")

            previous_line = line.number
        else:
            cfg.add_node(rid, block=FragmentView(src, start_line, previous_line + 1, start_line))

        return rid

    # Generate the dictionary containing label mappings
    label_dict = src.get_labels()

    # Instantiate the node id supplier
    id_sup = count()

    # Instantiate an empty di-graph for hosting the CFG
    cfg = DiGraph()

    # Initialize the dictionary mapping blocks' initial lines to nodes
    ancestors = {}

    # Initialize the graph with a special root node
    root_id = next(id_sup)
    cfg.add_node(root_id, external=True)
    ancestors[-1] = root_id

    # Initialize the return stack
    ret_stack = deque()
    ret_stack.append(-1)

    # Call the explorer on the entry point and append the resulting graph to the root node
    try:
        child_id = _explorer(label_dict[entry_point], ret_stack)
    except KeyError:
        raise ValueError("Entry point [" + entry_point + "] not found")

    cfg.add_edge(root_id, child_id, kind=Transition.U_JUMP)

    return cfg


def get_stepper(cfg: DiGraph, entry_pnt: int) -> Iterator[ASMLine]:
    """
    Step execution through the CFG.

    Given a CFG and an optional starting point (entry-point), generates an iterator that follows the program's execution
    flow.

    When confronted by the bifurcating edges of a conditional branch situation, callers can `.send()` the condition's
    truth value in order to select the branch to follow.

    If a node representing code not included in the represented source is encountered, the iterator emits the artificial
    directive:
        <non-local call $node_id>
    to signal the fact, then regularly proceeds by following the return arc.

    :param cfg: a control-flow graph representing the program
    :param entry_pnt: the entry point from which iteration should start, either in label form or as a line number
    :return: an iterator that produces ASMLine objects
    :raise ValueError: when the specified entry point does not belong to any node of the CFG
    """

    # Find the node containing the entry point
    # Be aware that the entry point *MUST* refer to an instruction; nodes only contain those.
    for nid in [n for n in cfg.nodes.keys() if "external" not in cfg.nodes[n]]:
        view: FragmentView = cfg.nodes[nid]["block"]
        if view.begin <= entry_pnt < view.end:
            current_node = nid
            break
    else:
        raise ValueError("Invalid entry-point: no statement at line " + str(entry_pnt) + "is contained in this graph")

    # Prepare objects for iteration
    block: FragmentView = cfg.nodes[current_node]["block"]
    line_iterator: Iterator[ASMLine] = to_line_iterator(block.iter(entry_pnt), entry_pnt)
    line: ASMLine = next(line_iterator)

    execute_jump = yield line
    while True:
        # Advance 'till the end of the current block
        for line in line_iterator:
            execute_jump = yield line

        # Identify any conditional branch
        conditional = None
        for t, s in [(cfg.edges[current_node, s]["kind"], s) for s in cfg.successors(current_node)]:
            if t is Transition.C_JUMP:
                conditional = s
            else:
                # We don't expect more than one other "default" path to follow
                current_node = s

        # Set the conditional branch's destination as the current node, if the caller told us so
        if conditional is not None and execute_jump:
            current_node = conditional

        # If we're back at node 0, then execution has finished
        if current_node == 0:
            return

        # If the node we reached is external, just yield a special value and advance to the node that follows it
        if "external" in cfg.nodes[current_node]:
            yield ASMLine(-1, Directive("<non-local call " + str(current_node) + ">"))
            current_node = next(cfg.successors(current_node))

        # Load the next block and continue iteration
        block = cfg.nodes[current_node]["block"]
        line_iterator = to_line_iterator(iter(block), block.begin)


def merge_points(cfg: DiGraph) -> FrozenSet[int]:
    """
    Find all the merge point in the CFG.

    A merge point is a node on which multiple directed edges converge.

    :arg cfg: the CFG representing a program
    :return: a frozen set containing all the merge points
    """

    # Node 0 represents the calling environment, so it must be excluded from the analysis
    return frozenset((n for n in cfg.nodes.keys() if n != 0 and cfg.in_degree(n) > 1))


def loop_back_nodes(cfg: DiGraph):
    """
    Find all the nodes of a CFG that are exclusively part of a loop.

    A node is exclusively part of a loop if it belongs only to those paths that traverse the back-loop of a cycle.

    :arg cfg: the CFG representation of a program
    :return: a frozen set of all the loop-exclusive nodes
    """

    # Node 0 closes an improper loop over the CFG, so it must be ignored
    cycle_nodes = frozenset(chain.from_iterable(simple_cycles(restricted_view(cfg, [0], []))))
    return frozenset(cycle_nodes.difference(chain.from_iterable(
        # For every path, its last component is node 0; therefore, we have to cut it.
        map(lambda l: l[:-1], all_simple_paths(cfg, 1, 0)))))
