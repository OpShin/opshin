from ast import *
from copy import copy
from collections import defaultdict

from ordered_set import OrderedSet

from ..util import CompilingNodeVisitor, CompilingNodeTransformer
from ..typed_ast import TypedAnnAssign, TypedFunctionDef, TypedClassDef, TypedName

"""
Removes assignments to variables that are never read
"""


class NameLoadCollector(CompilingNodeVisitor):
    step = "Collecting used variables"

    def __init__(self):
        self.loaded = defaultdict(int)

    def visit_Name(self, node: TypedName) -> None:
        if isinstance(node.ctx, Load):
            self.loaded[node.id] += 1

    def visit_Compare(self, node: Compare):
        self.generic_visit(node)
        for dunder_override in node.dunder_overrides:
            if dunder_override is not None:
                self.loaded[dunder_override.method_name] += 1

    def visit_ClassDef(self, node: TypedClassDef):
        # ignore the content (i.e. attribute names) of class definitions
        pass

    def visit_FunctionDef(self, node: TypedFunctionDef):
        # ignore the type hints of function arguments
        for s in node.body:
            self.visit(s)
        for v in node.typ.typ.bound_vars.keys():
            self.loaded[v] += 1
        if node.typ.typ.bind_self is not None:
            self.loaded[node.typ.typ.bind_self] += 1


class OptimizeRemoveDeadvars(CompilingNodeTransformer):
    step = "Removing unused variables"

    def __init__(self, validator_function_name: str):
        self.validator_function_name = validator_function_name
        super().__init__()

    loaded_vars = None

    def visit_Module(self, node: Module) -> Module:
        # repeat until no more change due to removal
        # i.e. b = a; c = b needs 2 passes to remove c and b
        node_cp = copy(node)
        self.loaded_vars = None
        while True:
            # collect all variable names
            collector = NameLoadCollector()
            collector.visit(node_cp)
            loaded_vars = OrderedSet(collector.loaded.keys()) | {
                self.validator_function_name + "_0"
            }
            # break if the set of loaded vars did not change -> set of vars to remove does also not change
            if loaded_vars == self.loaded_vars:
                break
            # remove unloaded ones
            self.loaded_vars = loaded_vars
            node_cp.body = [self.visit(s) for s in node_cp.body]
        return node_cp

    def visit_If(self, node: If):
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = [self.visit(s) for s in node.body]
        node_cp.orelse = [self.visit(s) for s in node.orelse]
        return node_cp

    def visit_While(self, node: While):
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = [self.visit(s) for s in node.body]
        node_cp.orelse = [self.visit(s) for s in node.orelse]
        return node_cp

    def visit_For(self, node: For):
        node_cp = copy(node)
        node_cp.body = [self.visit(s) for s in node.body]
        node_cp.orelse = [self.visit(s) for s in node.orelse]
        return node_cp

    def visit_Assign(self, node: Assign):
        if (
            len(node.targets) != 1
            or not isinstance(node.targets[0], Name)
            or node.targets[0].id in self.loaded_vars
        ):
            for t in node.targets:
                assert isinstance(
                    t, Name
                ), "Need to have name for dead var remover to work"
            return self.generic_visit(node)
        # variable is dead - replace with expression to preserve any side effects
        return Expr(node.value)

    def visit_AnnAssign(self, node: TypedAnnAssign):
        if (
            not isinstance(node.target, Name)
            or node.target.id in self.loaded_vars
            # only upcasts are safe!
            or not node.target.typ >= node.value.typ
        ):
            assert isinstance(
                node.target, Name
            ), "Need to have assignments to name for dead var remover to work"
            return self.generic_visit(node)
        # variable is dead - replace with expression to preserve any side effects
        return Expr(node.value)

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
