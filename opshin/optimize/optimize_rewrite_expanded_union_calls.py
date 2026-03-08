from ast import *
from copy import copy
from dataclasses import dataclass

from ..type_impls import FunctionType, InstanceType, UnionType
from ..util import CompilingNodeTransformer, read_vars
from .optimize_union_expansion import (
    get_specialized_function_name_for_types,
    split_specialized_function_name,
)


@dataclass(frozen=True)
class _ExpandedVariant:
    name: str
    typ: InstanceType


class OptimizeRewriteExpandedUnionCalls(CompilingNodeTransformer):
    step = "Rewriting expanded union calls"

    def __init__(self):
        super().__init__()
        self.variants_by_name = {}
        self.specialized_arg_positions_by_base_name = {}

    def _collect_typed_functions(self, body: list[stmt]) -> list[FunctionDef]:
        functions = []
        for s in body:
            if not isinstance(s, FunctionDef):
                continue
            if not (
                hasattr(s, "typ")
                and isinstance(s.typ, InstanceType)
                and isinstance(s.typ.typ, FunctionType)
            ):
                continue
            functions.append(s)
        return functions

    def _collect_expanded_variants(self, body: list[stmt]):
        variants_by_name = {}
        specialized_arg_positions_by_base_name = {}

        typed_functions = self._collect_typed_functions(body)
        for function in typed_functions:
            if split_specialized_function_name(function.name) is None:
                continue
            variants_by_name[function.name] = _ExpandedVariant(
                name=function.name,
                typ=function.typ,
            )

        for function in typed_functions:
            if split_specialized_function_name(function.name) is not None:
                continue
            specialized_positions = [
                i
                for i, argtyp in enumerate(function.typ.typ.argtyps)
                if isinstance(argtyp, InstanceType)
                and isinstance(argtyp.typ, UnionType)
            ]
            if specialized_positions:
                specialized_arg_positions_by_base_name[function.name] = (
                    specialized_positions
                )

        return variants_by_name, specialized_arg_positions_by_base_name

    def _rewrite_sequence(self, body: list[stmt]) -> list[stmt]:
        prev_variants = dict(self.variants_by_name)
        prev_positions = dict(self.specialized_arg_positions_by_base_name)
        variants_by_name, specialized_arg_positions_by_base_name = (
            self._collect_expanded_variants(body)
        )
        self.variants_by_name.update(variants_by_name)
        self.specialized_arg_positions_by_base_name.update(
            specialized_arg_positions_by_base_name
        )
        try:
            rewritten = [self.visit(stmt) for stmt in body]
            read_names = set(read_vars(Module(body=rewritten, type_ignores=[])))
            return [
                stmt
                for stmt in rewritten
                if not (
                    isinstance(stmt, FunctionDef)
                    and hasattr(stmt, "expanded_variants")
                    and stmt.name not in read_names
                )
            ]
        finally:
            self.variants_by_name = prev_variants
            self.specialized_arg_positions_by_base_name = prev_positions

    def visit_Call(self, node: Call) -> Call:
        node = self.generic_visit(node)
        if not isinstance(node.func, Name):
            return node

        specialized_positions = self.specialized_arg_positions_by_base_name.get(
            node.func.id
        )
        if specialized_positions is None:
            return node

        specialized_name = get_specialized_function_name_for_types(
            node.func.id,
            [arg.typ for arg in node.args],
            specialized_argument_positions=specialized_positions,
        )
        variant = self.variants_by_name.get(specialized_name)
        if variant is None:
            return node

        argtyps = variant.typ.typ.argtyps
        if len(node.args) != len(argtyps):
            return node
        if any(actual.typ != expected for actual, expected in zip(node.args, argtyps)):
            return node

        node.func.id = variant.name
        node.func.typ = variant.typ
        return node

    def visit_Module(self, node: Module) -> Module:
        module = copy(node)
        module.body = list(node.body)
        module.type_ignores = list(getattr(node, "type_ignores", []))
        module.body = self._rewrite_sequence(module.body)
        return module

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        function = copy(node)
        function.body = self._rewrite_sequence(list(node.body))
        return function

    def visit_If(self, node: If) -> If:
        typed_if = copy(node)
        typed_if.body = self._rewrite_sequence(list(node.body))
        typed_if.orelse = self._rewrite_sequence(list(node.orelse))
        return typed_if

    def visit_While(self, node: While) -> While:
        typed_while = copy(node)
        typed_while.body = self._rewrite_sequence(list(node.body))
        typed_while.orelse = self._rewrite_sequence(list(node.orelse))
        return typed_while

    def visit_For(self, node: For) -> For:
        typed_for = copy(node)
        typed_for.body = self._rewrite_sequence(list(node.body))
        typed_for.orelse = self._rewrite_sequence(list(node.orelse))
        return typed_for
