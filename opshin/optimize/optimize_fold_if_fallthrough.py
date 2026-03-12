from __future__ import annotations
from ast import *
from copy import copy

from ..typed_util import (
    ScopedSequenceNodeTransformer,
    annotate_compound_statement_fallthrough,
)

"""
If exactly one branch of an if-statement can fall through, fold the following
statements in the enclosing sequence into that branch.
"""


class OptimizeFoldIfFallthrough(ScopedSequenceNodeTransformer):
    step = "Folding trailing statements into sole fallthrough if-branches"

    def fold_sequence(self, statements):
        folded = []
        i = 0
        while i < len(statements):
            if statements[i] is None:
                i += 1
                continue
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
                    folded.append(annotate_compound_statement_fallthrough(stmt))
                    break
            folded.append(stmt)
            i += 1
        return folded

    def visit_Module(self, node: Module) -> Module:
        node_cp = super().visit_Module(node)
        node_cp.body = self.fold_sequence(node_cp.body)
        return annotate_compound_statement_fallthrough(node_cp)

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        node_cp = super().visit_FunctionDef(node)
        node_cp.body = self.fold_sequence(node_cp.body)
        return annotate_compound_statement_fallthrough(node_cp)

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        node_cp = super().visit_ClassDef(node)
        node_cp.body = self.fold_sequence(node_cp.body)
        return annotate_compound_statement_fallthrough(node_cp)

    def visit_If(self, node: If) -> If:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.orelse = self.fold_sequence(node.orelse)
        return annotate_compound_statement_fallthrough(node_cp)

    def visit_While(self, node: While) -> While:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.orelse = self.fold_sequence(node.orelse)
        return annotate_compound_statement_fallthrough(node_cp)

    def visit_For(self, node: For) -> For:
        node_cp = copy(node)
        node_cp.target = self.visit(node.target)
        node_cp.iter = self.visit(node.iter)
        node_cp.body = self.fold_sequence(node.body)
        node_cp.orelse = self.fold_sequence(node.orelse)
        return annotate_compound_statement_fallthrough(node_cp)
