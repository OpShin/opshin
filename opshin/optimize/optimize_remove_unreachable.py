from ast import *
from copy import copy

from ..util import CompilingNodeTransformer

"""
Removes statements that are unreachable because a previous statement in the same
sequence is known not to fall through.
"""


class OptimizeRemoveUnreachable(CompilingNodeTransformer):
    step = "Removing unreachable statements"

    @staticmethod
    def visit_sequence(statements, visitor):
        visited = []
        for stmt in statements:
            stmt_cp = visitor.visit(stmt)
            if stmt_cp is None:
                continue
            visited.append(stmt_cp)
            if not getattr(stmt_cp, "can_fall_through", True):
                break
        return visited

    def visit_Module(self, node: Module) -> Module:
        node_cp = copy(node)
        node_cp.body = self.visit_sequence(node.body, self)
        return node_cp

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        node_cp = copy(node)
        node_cp.body = self.visit_sequence(node.body, self)
        return node_cp

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        node_cp = copy(node)
        node_cp.body = self.visit_sequence(node.body, self)
        return node_cp

    def visit_If(self, node: If) -> If:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = self.visit_sequence(node.body, self)
        node_cp.orelse = self.visit_sequence(node.orelse, self)
        return node_cp

    def visit_While(self, node: While) -> While:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = self.visit_sequence(node.body, self)
        node_cp.orelse = self.visit_sequence(node.orelse, self)
        return node_cp

    def visit_For(self, node: For) -> For:
        node_cp = copy(node)
        node_cp.target = self.visit(node.target)
        node_cp.iter = self.visit(node.iter)
        node_cp.body = self.visit_sequence(node.body, self)
        node_cp.orelse = self.visit_sequence(node.orelse, self)
        return node_cp
