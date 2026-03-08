from ast import *
from copy import copy

from ..util import CompilingNodeTransformer

"""
If exactly one branch of an if-statement can fall through, fold the following
statements in the enclosing sequence into that branch.
"""


def sequence_can_fall_through(statements):
    for stmt in statements:
        if not getattr(stmt, "can_fall_through", True):
            return False
    return True


class OptimizeFoldIfFallthrough(CompilingNodeTransformer):
    step = "Folding trailing statements into sole fallthrough if-branches"

    def fold_sequence(self, statements):
        folded = []
        i = 0
        while i < len(statements):
            stmt = self.visit(statements[i])
            if stmt is None:
                i += 1
                continue
            if isinstance(stmt, If):
                body_can_fall_through = getattr(stmt, "body_can_fall_through", True)
                orelse_can_fall_through = getattr(stmt, "orelse_can_fall_through", True)
                if body_can_fall_through != orelse_can_fall_through and i + 1 < len(
                    statements
                ):
                    trailing = statements[i + 1 :]
                    if body_can_fall_through:
                        stmt.body = self.fold_sequence(stmt.body + trailing)
                    else:
                        stmt.orelse = self.fold_sequence(stmt.orelse + trailing)
                    stmt.body_can_fall_through = sequence_can_fall_through(stmt.body)
                    stmt.orelse_can_fall_through = sequence_can_fall_through(
                        stmt.orelse
                    )
                    stmt.can_fall_through = (
                        stmt.body_can_fall_through or stmt.orelse_can_fall_through
                    )
                    folded.append(stmt)
                    break
            folded.append(stmt)
            i += 1
        return folded

    def visit_Module(self, node: Module) -> Module:
        node_cp = copy(node)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.can_fall_through = sequence_can_fall_through(node_cp.body)
        return node_cp

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        node_cp = copy(node)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.body_can_fall_through = sequence_can_fall_through(node_cp.body)
        node_cp.can_fall_through = True
        return node_cp

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        node_cp = copy(node)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.body_can_fall_through = sequence_can_fall_through(node_cp.body)
        node_cp.can_fall_through = True
        return node_cp

    def visit_If(self, node: If) -> If:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.orelse = self.fold_sequence(node.orelse)
        node_cp.body_can_fall_through = sequence_can_fall_through(node_cp.body)
        node_cp.orelse_can_fall_through = sequence_can_fall_through(node_cp.orelse)
        node_cp.can_fall_through = (
            node_cp.body_can_fall_through or node_cp.orelse_can_fall_through
        )
        return node_cp

    def visit_While(self, node: While) -> While:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.orelse = self.fold_sequence(node.orelse)
        node_cp.body_can_fall_through = sequence_can_fall_through(node_cp.body)
        node_cp.orelse_can_fall_through = sequence_can_fall_through(node_cp.orelse)
        node_cp.can_fall_through = node_cp.orelse_can_fall_through
        return node_cp

    def visit_For(self, node: For) -> For:
        node_cp = copy(node)
        node_cp.target = self.visit(node.target)
        node_cp.iter = self.visit(node.iter)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.orelse = self.fold_sequence(node.orelse)
        node_cp.body_can_fall_through = sequence_can_fall_through(node_cp.body)
        node_cp.orelse_can_fall_through = sequence_can_fall_through(node_cp.orelse)
        node_cp.can_fall_through = node_cp.orelse_can_fall_through
        return node_cp
