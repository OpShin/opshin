import ast
from ast import AST, Compare, Constant, Lambda, Load, Name
from _ast import ClassDef, FunctionDef
from collections import defaultdict
from copy import copy

from .type_impls import FunctionType, InstanceType
from .typed_ast import TypedClassDef, TypedFunctionDef, TypedName
from .util import CompilingNodeTransformer, CompilingNodeVisitor


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


class NameLoadCollector(CompilingNodeVisitor):
    step = "Collecting used variables"

    def __init__(self):
        self.loaded = defaultdict(int)

    def visit_Name(self, node: TypedName) -> None:
        if isinstance(node.ctx, Load):
            self.loaded[node.id] += 1

    def visit_Compare(self, node: Compare):
        self.generic_visit(node)
        for dunder_override in node.dunder_overrides:
            if dunder_override is not None:
                self.loaded[dunder_override.method_name] += 1

    def visit_ClassDef(self, node: TypedClassDef):
        # ignore the content (i.e. attribute names) of class definitions
        pass

    def visit_FunctionDef(self, node: TypedFunctionDef):
        # ignore the type hints of function arguments
        for s in node.body:
            self.visit(s)
        for v in node.typ.typ.bound_vars.keys():
            self.loaded[v] += 1
        if node.typ.typ.bind_self is not None:
            self.loaded[node.typ.typ.bind_self] += 1


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
