import ast
from _ast import ClassDef, FunctionDef
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


def statement_can_fall_through(node: ast.stmt) -> bool:
    return getattr(node, "can_fall_through", True)


def sequence_can_fall_through(body: list[ast.stmt]) -> bool:
    return all(node is None or statement_can_fall_through(node) for node in body)


def annotate_compound_statement_fallthrough(node: ast.AST) -> ast.AST:
    if isinstance(node, ast.Module):
        node.can_fall_through = sequence_can_fall_through(node.body)
        return node
    if isinstance(node, (FunctionDef, ClassDef)):
        node.body_can_fall_through = sequence_can_fall_through(node.body)
        node.can_fall_through = True
        return node
    if isinstance(node, ast.If):
        node.body_can_fall_through = sequence_can_fall_through(node.body)
        node.orelse_can_fall_through = sequence_can_fall_through(node.orelse)
        node.can_fall_through = (
            node.body_can_fall_through or node.orelse_can_fall_through
        )
        return node
    if isinstance(node, (ast.While, ast.For)):
        node.body_can_fall_through = sequence_can_fall_through(node.body)
        node.orelse_can_fall_through = sequence_can_fall_through(node.orelse)
        # Without break support, normal loop completion always enters the else branch.
        node.can_fall_through = node.orelse_can_fall_through
        return node
    raise TypeError(f"Unsupported node type for fallthrough annotation: {type(node)}")


class ScopedSequenceNodeTransformer(CompilingNodeTransformer):
    """Rewrite nested statement sequences while preserving the surrounding node."""

    def visit_sequence(self, body: list[ast.stmt]) -> list[ast.stmt]:
        rewritten = []
        for node in body:
            if node is None:
                continue
            updated = self.visit(node)
            if updated is None:
                continue
            rewritten.append(updated)
        return rewritten

    def visit_Module(self, node: ast.Module) -> ast.Module:
        module = copy(node)
        module.body = self.visit_sequence(list(node.body))
        module.type_ignores = list(getattr(node, "type_ignores", []))
        return module

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        function = copy(node)
        function.body = self.visit_sequence(list(node.body))
        return function

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        class_def = copy(node)
        class_def.body = self.visit_sequence(list(node.body))
        return class_def

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


class FlatteningScopedSequenceNodeTransformer(ScopedSequenceNodeTransformer):
    """Like ScopedSequenceNodeTransformer, but flatten list-valued statement rewrites."""

    def visit_sequence(self, body: list[ast.stmt]) -> list[ast.stmt]:
        rewritten = []
        for node in body:
            if node is None:
                continue
            updated = self.visit(node)
            if updated is None:
                continue
            if isinstance(updated, list):
                rewritten.extend(updated)
                continue
            rewritten.append(updated)
        return rewritten
