from ast import *
from copy import copy
from typing import Any, Union

from ..typed_util import FlatteningScopedSequenceNodeTransformer

"""
Removes if/while branches that are never executed
"""


class OptimizeRemoveDeadConditions(FlatteningScopedSequenceNodeTransformer):
    def expression_guaranteed_tf(self, expr: expr) -> Union[bool, None]:
        """
        Returns True if the expression is guaranteed to be truthy.
        Returns False if the expression is guaranteed to be falsy.
        Returns None if it cannot be determined.

        Needs to be run after self.visit has been called on expr.
        """
        if isinstance(expr, Constant):
            return bool(expr.value)
        return None

    def visit_If(self, node: If) -> Any:
        node = copy(node)
        node.test = self.visit(node.test)
        node.body = self.visit_sequence(node.body)
        node.orelse = self.visit_sequence(node.orelse)
        test_value = self.expression_guaranteed_tf(node.test)
        if test_value is True:
            return node.body
        if test_value is False:
            return node.orelse
        return node

    def visit_While(self, node: While) -> Any:
        node = copy(node)
        node.test = self.visit(node.test)
        node.body = self.visit_sequence(node.body)
        node.orelse = self.visit_sequence(node.orelse)
        test_value = self.expression_guaranteed_tf(node.test)
        if test_value is True:
            raise ValueError(
                "While loop with constant True condition is not allowed (infinite loop)"
            )
        if test_value is False:
            return node.orelse
        return node

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
            if isinstance(ex.op, And):
                return next((v for v in ex.values if not v.value), ex.values[-1])
            elif isinstance(ex.op, Or):
                return next((v for v in ex.values if v.value), ex.values[-1])
        if isinstance(ex.op, Or):
            new_values = []
            for index, value in enumerate(ex.values):
                if index == len(ex.values) - 1:
                    new_values.append(value)
                    continue
                if isinstance(value, Constant) and value.value:
                    new_values.append(value)
                    ex.values = new_values
                    break
                if isinstance(value, Constant):
                    continue
                new_values.append(value)
            else:
                ex.values = new_values
        elif isinstance(ex.op, And):
            new_values = []
            for index, value in enumerate(ex.values):
                if index == len(ex.values) - 1:
                    new_values.append(value)
                    continue
                if isinstance(value, Constant) and not value.value:
                    new_values.append(value)
                    ex.values = new_values
                    break
                if isinstance(value, Constant):
                    continue
                new_values.append(value)
            else:
                ex.values = new_values
        if len(ex.values) == 1:
            return ex.values[0]
        return ex
