from ast import *
from copy import deepcopy, copy
from typing import Any, Union

from ..util import CompilingNodeTransformer

"""
Removes if/while branches that are never executed
"""


class ExpressionSimplifier(CompilingNodeTransformer):

    def expression_guaranteed_tf(self, expr: expr) -> Union[bool, None]:
        """
        Returns True if the expression is guaranteed to be truthy
        Returns False if the expression is guaranteed to be falsy
        Returns None if it cannot be determined

        Needs to be run after self.visit has been called on expr
        """
        if isinstance(expr, Constant):
            return expr.value
        return None

    def visit_IfExp(self, node: IfExp) -> expr:
        ex = copy(node)
        ex.test = self.visit(ex.test)
        ex.body = self.visit(ex.body)
        ex.orelse = self.visit(ex.orelse)

        test_value = self.expression_guaranteed_tf(ex.test)
        if test_value is True:
            return ex.body
        if test_value is False:
            return ex.orelse
        return ex

    def visit_UnaryOp(self, node: UnaryOp) -> expr:
        ex = copy(node)
        ex.operand = self.visit(ex.operand)

        if isinstance(ex.op, Not):
            if isinstance(ex.operand, Constant):
                return Constant(value=not bool(ex.operand.value))
        return ex

    def visit_BoolOp(self, node: BoolOp) -> expr:
        ex = copy(node)
        ex.values = [self.visit(v) for v in ex.values]
        if all(isinstance(v, Constant) for v in ex.values):
            values = [bool(v.value) for v in ex.values]
            if isinstance(ex.op, And):
                return Constant(value=all(values))
            elif isinstance(ex.op, Or):
                return Constant(value=any(values))

        # Partial simplification: drop neutral constants
        # e.g. in `x or True`, return Constant(True)
        # e.g. in `x and False`, return Constant(False)
        if isinstance(ex.op, And):
            for v in ex.values:
                if isinstance(v, Constant) and not v.value:
                    return Constant(value=False)
            ex.values = [
                v for v in ex.values if not (isinstance(v, Constant) and v.value)
            ]
        elif isinstance(ex.op, Or):
            for v in ex.values:
                if isinstance(v, Constant) and v.value:
                    return Constant(value=True)
            ex.values = [
                v for v in ex.values if not (isinstance(v, Constant) and not v.value)
            ]
        if len(ex.values) == 1:
            return ex.values[0]
        return ex


def simplify_expression(ex: expr) -> expr:
    simplifier = ExpressionSimplifier()
    return simplifier.visit(ex)


class OptimizeRemoveDeadConditions(CompilingNodeTransformer):

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        node = copy(node)
        node.body = self.visit_sequence(node.body)
        return node

    def visit_sequence(self, stmts):
        new_stmts = []
        for stmt in stmts:
            s = self.visit(stmt)
            if s is None:
                continue
            if isinstance(s, list):
                new_stmts.extend(s)
            else:
                new_stmts.append(s)
        return new_stmts

    def visit_If(self, node: If) -> Any:
        node = copy(node)
        node.test = simplify_expression(node.test)
        node.body = self.visit_sequence(node.body)
        node.orelse = self.visit_sequence(node.orelse)
        if isinstance(node.test, Constant):
            if node.test.value:
                return node.body
            else:
                return node.orelse
        return node

    def visit_While(self, node: While) -> Any:
        node = copy(node)
        node.test = simplify_expression(node.test)
        node.body = self.visit_sequence(node.body)
        node.orelse = self.visit_sequence(node.orelse)
        if isinstance(node.test, Constant):
            if node.test.value:
                raise ValueError(
                    "While loop with constant True condition is not allowed (infinite loop)"
                )
            else:
                return node.orelse
        return node

    def visit_IfExp(self, node: IfExp) -> Any:
        node = copy(node)
        node.test = simplify_expression(node.test)
        node.body = self.visit(node.body)
        node.orelse = self.visit(node.orelse)

        # Simplify if the test condition is a constant
        if isinstance(node.test, Constant):
            if node.test.value:
                return node.body
            else:
                return node.orelse

        return node
