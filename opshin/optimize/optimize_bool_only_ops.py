import ast
from copy import copy

from ..type_impls import (
    BoolImpl,
    BoolInstanceType,
    PolymorphicFunctionInstanceType,
)
from ..util import CompilingNodeTransformer


class OptimizeBoolOnlyOps(CompilingNodeTransformer):
    """Lower value-discarded and/or expressions to ordinary boolean operations."""

    step = "Using boolean-only and/or operations"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node = copy(node)
        node.body = [self.visit(statement) for statement in node.body]
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        node = copy(node)
        node.body = [self.visit(statement) for statement in node.body]
        return node

    @staticmethod
    def negate(node: ast.expr) -> ast.UnaryOp:
        negated = ast.UnaryOp(op=ast.Not(), operand=node)
        negated.typ = BoolInstanceType
        return ast.copy_location(negated, node)

    @classmethod
    def lower_bool_op(cls, node: ast.BoolOp, bool_call: ast.Call) -> ast.expr:
        result = copy(bool_call)
        result.args = [node.values[-1]]
        ast.copy_location(result, node.values[-1])

        for value in reversed(node.values[:-1]):
            constant = ast.Constant(value=isinstance(node.op, ast.Or))
            constant.typ = BoolInstanceType
            ast.copy_location(constant, value)
            if isinstance(node.op, ast.And):
                body, orelse = constant, result
            else:
                body, orelse = result, constant
            result = ast.IfExp(
                test=cls.negate(value),
                body=body,
                orelse=orelse,
            )
            result.typ = BoolInstanceType
            ast.copy_location(result, value)
        return result

    def visit_Call(self, node: ast.Call) -> ast.expr:
        node = self.generic_visit(copy(node))
        if not (
            isinstance(node.func.typ, PolymorphicFunctionInstanceType)
            and isinstance(node.func.typ.polymorphic_function, BoolImpl)
            and len(node.args) == 1
            and isinstance(node.args[0], ast.BoolOp)
        ):
            return node

        operand = node.args[0]
        if operand.typ == BoolInstanceType:
            return node
        return ast.copy_location(self.lower_bool_op(operand, node), node)
