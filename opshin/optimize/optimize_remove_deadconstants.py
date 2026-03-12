from ast import *
from copy import copy

from ..util import CompilingNodeTransformer
from ..type_inference import INITIAL_SCOPE
from .optimize_remove_deadvars import SafeOperationVisitor

"""
Removes expressions that are safely side effect free in sequences of statements
(e.g. constants, names, lambdas, string comments)
"""


class OptimizeRemoveDeadConstants(CompilingNodeTransformer):
    step = "Removing dead expressions"

    guaranteed_avail_names = [
        list(INITIAL_SCOPE.keys()) + ["isinstance", "Union", "Dict", "List"]
    ]

    def enter_scope(self):
        self.guaranteed_avail_names.append([])

    def exit_scope(self):
        self.guaranteed_avail_names.pop()

    def set_guaranteed(self, name: str):
        self.guaranteed_avail_names[-1].append(name)

    def visit_stmts(self, stmts):
        res = []
        for s in stmts:
            r = self.visit(s)
            if r is not None:
                res.append(r)
        return res

    def visit_Module(self, node: Module):
        node_cp = copy(node)
        self.enter_scope()
        node_cp.body = self.visit_stmts(node.body)
        self.exit_scope()
        return node_cp

    def visit_Expr(self, node: Expr):
        if SafeOperationVisitor(sum(self.guaranteed_avail_names, [])).visit(node.value):
            return None
        return node

    def visit_FunctionDef(self, node: FunctionDef):
        node_cp = copy(node)
        self.set_guaranteed(node.name)
        self.enter_scope()
        for a in node.args.args:
            self.set_guaranteed(a.arg)
        node_cp.body = self.visit_stmts(node.body)
        self.exit_scope()
        return node_cp

    def visit_Assign(self, node: Assign):
        for t in node.targets:
            if isinstance(t, Name):
                self.set_guaranteed(t.id)
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: AnnAssign):
        if isinstance(node.target, Name):
            self.set_guaranteed(node.target.id)
        return self.generic_visit(node)
