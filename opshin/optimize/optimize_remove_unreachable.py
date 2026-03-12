from __future__ import annotations
from ast import *
from copy import copy

from ..typed_util import ScopedSequenceNodeTransformer

"""
Removes statements that are unreachable because a previous statement in the same
sequence is known not to fall through.
"""


class OptimizeRemoveUnreachable(ScopedSequenceNodeTransformer):
    step = "Removing unreachable statements"

    def visit_sequence(self, statements):
        visited = []
        for stmt in statements:
            if stmt is None:
                continue
            stmt_cp = self.visit(stmt)
            if stmt_cp is None:
                continue
            visited.append(stmt_cp)
            if not getattr(stmt_cp, "can_fall_through", True):
                break
        return visited

    def visit_If(self, node: If) -> If:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = self.visit_sequence(node.body)
        node_cp.orelse = self.visit_sequence(node.orelse)
        return node_cp

    def visit_While(self, node: While) -> While:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = self.visit_sequence(node.body)
        node_cp.orelse = self.visit_sequence(node.orelse)
        return node_cp

    def visit_For(self, node: For) -> For:
        node_cp = copy(node)
        node_cp.target = self.visit(node.target)
        node_cp.iter = self.visit(node.iter)
        node_cp.body = self.visit_sequence(node.body)
        node_cp.orelse = self.visit_sequence(node.orelse)
        return node_cp
