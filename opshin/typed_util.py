import ast
from _ast import FunctionDef
from copy import copy

from .type_impls import FunctionType, InstanceType
from .util import CompilingNodeTransformer


def collect_typed_functions(body: list[ast.stmt]) -> list[FunctionDef]:
    return [
        node
        for node in body
        if isinstance(node, FunctionDef)
        and hasattr(node, "typ")
        and isinstance(node.typ, InstanceType)
        and isinstance(node.typ.typ, FunctionType)
    ]


class ScopedSequenceNodeTransformer(CompilingNodeTransformer):
    """Rewrite nested statement sequences while preserving the surrounding node."""

    def visit_sequence(self, body: list[ast.stmt]) -> list[ast.stmt]:
        return [self.visit(node) for node in body]

    def visit_Module(self, node: ast.Module) -> ast.Module:
        module = copy(node)
        module.body = self.visit_sequence(list(node.body))
        module.type_ignores = list(getattr(node, "type_ignores", []))
        return module

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        function = copy(node)
        function.body = self.visit_sequence(list(node.body))
        return function

    def visit_If(self, node: ast.If) -> ast.If:
        typed_if = copy(node)
        typed_if.body = self.visit_sequence(list(node.body))
        typed_if.orelse = self.visit_sequence(list(node.orelse))
        return typed_if

    def visit_While(self, node: ast.While) -> ast.While:
        typed_while = copy(node)
        typed_while.body = self.visit_sequence(list(node.body))
        typed_while.orelse = self.visit_sequence(list(node.orelse))
        return typed_while

    def visit_For(self, node: ast.For) -> ast.For:
        typed_for = copy(node)
        typed_for.body = self.visit_sequence(list(node.body))
        typed_for.orelse = self.visit_sequence(list(node.orelse))
        return typed_for
