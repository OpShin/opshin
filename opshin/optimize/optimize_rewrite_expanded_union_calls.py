from ast import *
from copy import copy
from dataclasses import dataclass

from ..type_impls import FunctionType, InstanceType, UnionType
from ..util import CompilingNodeTransformer
from .optimize_rewrite_function_closures import OptimizeRewriteFunctionClosures
from .optimize_union_expansion import (
    get_specialized_function_name_for_types,
    split_specialized_function_name,
)


@dataclass(frozen=True)
class _ExpandedVariant:
    name: str
    typ: InstanceType


class OptimizeRewriteExpandedUnionCalls(OptimizeRewriteFunctionClosures):
    step = "Rewriting expanded union calls"

    def __init__(self):
        super().__init__()
        self.variants_by_name = {}
        self.specialized_arg_positions_by_base_name = {}

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

        self.variants_by_name = variants_by_name
        self.specialized_arg_positions_by_base_name = (
            specialized_arg_positions_by_base_name
        )

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

        self._collect_expanded_variants(module.body)
        module.body = [self.visit(stmt) for stmt in module.body]
        self._update_function_bound_vars(module.body)
        return module
