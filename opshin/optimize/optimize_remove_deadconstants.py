from ast import *
from copy import copy

from ..util import CompilingNodeVisitor, CompilingNodeTransformer
from ..type_inference import INITIAL_SCOPE

"""
Removes expressions that are safely side effect free in sequences of statements
(e.g. constants, names, lambdas, string comments)
"""


class SafeOperationVisitor(CompilingNodeVisitor):
    step = "Collecting computations that can not throw errors"

    def __init__(self, guaranteed_names):
        self.guaranteed_names = guaranteed_names

    def generic_visit(self, node: AST) -> bool:
        # generally every operation is unsafe except we whitelist it
        return False

    def visit_Lambda(self, node: Lambda) -> bool:
        # lambda definition is fine as it actually doesn't compute anything
        return True

    def visit_Constant(self, node: Constant) -> bool:
        # Constants can not fail
        return True

    def visit_RawPlutoExpr(self, node) -> bool:
        # these expressions are not evaluated further
        return True

    def visit_Name(self, node: Name) -> bool:
        return node.id in self.guaranteed_names


class OptimizeRemoveDeadConstants(CompilingNodeTransformer):
    step = "Removing dead expressions"

    def __init__(self):
        self.guaranteed_avail_names = [
            set(INITIAL_SCOPE.keys()) | {"isinstance", "Union", "Dict", "List"}
        ]

    def enter_scope(self):
        self.guaranteed_avail_names.append(set())

    def exit_scope(self):
        self.guaranteed_avail_names.pop()

    def set_guaranteed(self, name: str):
        self.guaranteed_avail_names[-1].add(name)

    def visit_conditional_sequence(self, stmts, initially_guaranteed):
        self.guaranteed_avail_names[-1] = set(initially_guaranteed)
        result = self.visit_stmts(stmts)
        return result, set(self.guaranteed_avail_names[-1])

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
        guaranteed_names = set().union(*self.guaranteed_avail_names)
        if SafeOperationVisitor(guaranteed_names).visit(node.value):
            return None
        return node

    def visit_If(self, node: If):
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        initially_guaranteed = set(self.guaranteed_avail_names[-1])
        node_cp.body, body_guaranteed = self.visit_conditional_sequence(
            node.body, initially_guaranteed
        )
        node_cp.orelse, orelse_guaranteed = self.visit_conditional_sequence(
            node.orelse, initially_guaranteed
        )
        self.guaranteed_avail_names[-1] = body_guaranteed & orelse_guaranteed
        return node_cp

    def visit_While(self, node: While):
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        initially_guaranteed = set(self.guaranteed_avail_names[-1])
        node_cp.body, _ = self.visit_conditional_sequence(
            node.body, initially_guaranteed
        )
        node_cp.orelse, _ = self.visit_conditional_sequence(
            node.orelse, initially_guaranteed
        )
        self.guaranteed_avail_names[-1] = initially_guaranteed
        return node_cp

    def visit_For(self, node: For):
        node_cp = copy(node)
        node_cp.target = self.visit(node.target)
        node_cp.iter = self.visit(node.iter)
        initially_guaranteed = set(self.guaranteed_avail_names[-1])
        node_cp.body, _ = self.visit_conditional_sequence(
            node.body, initially_guaranteed
        )
        node_cp.orelse, _ = self.visit_conditional_sequence(
            node.orelse, initially_guaranteed
        )
        self.guaranteed_avail_names[-1] = initially_guaranteed
        return node_cp

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
        node = self.generic_visit(node)
        for t in node.targets:
            if isinstance(t, Name):
                self.set_guaranteed(t.id)
        return node

    def visit_AnnAssign(self, node: AnnAssign):
        node = self.generic_visit(node)
        if isinstance(node.target, Name):
            self.set_guaranteed(node.target.id)
        return node
