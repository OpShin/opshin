from ast import *
from copy import copy
from collections import defaultdict

from ..util import CompilingNodeVisitor, CompilingNodeTransformer

"""
Removes assignments to variables that are never read
"""


class NameLoadCollector(CompilingNodeVisitor):
    step = "Collecting used variables"

    def __init__(self):
        self.loaded = defaultdict(int)

    def visit_Name(self, node: Name) -> None:
        if isinstance(node.ctx, Load):
            self.loaded[node.id] += 1

    def visit_ClassDef(self, node: ClassDef):
        # ignore the content (i.e. attribute names) of class definitions
        pass

    def visit_FunctionDef(self, node: FunctionDef):
        # ignore the type hints of function arguments
        for s in node.body:
            self.visit(s)


class OptimizeRemoveDeadvars(CompilingNodeTransformer):
    step = "Removing unused variables"

    loaded_vars = None

    def visit_Module(self, node: Module) -> Module:
        # collect all variable names
        collector = NameLoadCollector()
        collector.visit(node)
        self.loaded_vars = set(collector.loaded.keys())
        self.loaded_vars |= {"validator"}
        node_cp = copy(node)
        node_cp.body = [self.visit(s) for s in node.body]
        return node_cp

    def visit_Assign(self, node: Assign):
        if (
            len(node.targets) != 1
            or not isinstance(node.targets[0], Name)
            or node.targets[0].id in self.loaded_vars
        ):
            return self.generic_visit(node)
        return Pass()

    def visit_AnnAssign(self, node: AnnAssign):
        if not isinstance(node.target, Name) or node.target.id in self.loaded_vars:
            return self.generic_visit(node)
        return Pass()

    def visit_ClassDef(self, node: ClassDef):
        if node.name in self.loaded_vars:
            return node
        return Pass()

    def visit_FunctionDef(self, node: FunctionDef):
        node_cp = copy(node)
        if node.name in self.loaded_vars:
            node_cp.body = [self.visit(s) for s in node.body]
            return node_cp
        return Pass()
