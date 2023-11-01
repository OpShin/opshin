from typing import Optional, Union

from ast import *
from copy import copy
from collections import defaultdict

from ..util import CompilingNodeVisitor, CompilingNodeTransformer, DefinedTimesVisitor
from ..type_inference import INITIAL_SCOPE
from ..typed_ast import TypedAnnAssign

"""
Removes assignments to variables that are never read
"""


class VariableValueCollector(CompilingNodeVisitor):
    values = defaultdict(list)

    def __init__(self, constants):
        self.constants = constants

    def visit_Assign(self, node: Assign) -> None:
        assert len(node.targets) == 1
        t = node.targets[0]
        if isinstance(t, Name) and t.id in self.constants:
            self.values[t.id].append(node.value)
            return None
        return self.generic_visit(node)


class OptimizeInlineConstvars(CompilingNodeTransformer):
    step = "Inline variables that are constant (i.e. written only once)"

    constants = set()
    constant_value = {}

    def visit_Module(self, node: Module) -> Module:
        # repeat until no more change due to removal
        # i.e. b = a; c = b needs 2 passes to remove c and b
        node_cp = copy(node)
        # collect all variable names
        constant_collector = DefinedTimesVisitor()
        constant_collector.visit(node)
        constants = constant_collector.vars
        # if it is only assigned exactly once, it must be a constant (due to immutability)
        self.constants = {c for c, i in constants.items() if i == 1}
        constant_value_collector = VariableValueCollector(self.constants)
        constant_value_collector.visit(node)
        self.constant_value = constant_value_collector.values
        node_cp.body = [self.visit(s) for s in node_cp.body]
        return node_cp

    def visit_Assign(self, node: Assign) -> Optional[Assign]:
        assert len(node.targets) == 1
        t = node.targets[0]
        if isinstance(t, Name) and t.id in self.constants:
            return None
        return self.generic_visit(node)

    def visit_Name(self, node: Name) -> Union[Name, expr]:
        if isinstance(node.ctx, Load) and node.id in self.constants:
            assert (
                node.id in self.constant_value
            ), f"Variable {node.id} not in constant_value, accessed before assignment"
            return self.visit(self.constant_value[node.id][0])
        return self.generic_visit(node)
