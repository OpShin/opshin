from __future__ import annotations
from ast import *
from dataclasses import dataclass

from ..type_impls import InstanceType, UnionType
from ..typed_util import (
    ScopedSequenceNodeTransformer,
    collect_typed_functions,
)
from ..optimize.optimize_union_expansion import (
    get_specialized_function_name_for_types,
    split_specialized_function_name,
)


@dataclass(frozen=True)
class _ExpandedVariant:
    name: str
    typ: InstanceType


class RewriteExpandedUnionCalls(ScopedSequenceNodeTransformer):
    # This pass keeps track of specialized union variants in the current nested
    # statement sequence, so calls can be rewritten even when the expanded
    # functions live inside another function or control-flow block.
    step = "Rewriting expanded union calls"

    def __init__(self):
        super().__init__()
        self.variants_by_name = {}
        self.specialized_arg_positions_by_base_name = {}

    def _collect_expanded_variants(self, body: list[stmt]):
        variants_by_name = {}
        specialized_arg_positions_by_base_name = {}

        typed_functions = collect_typed_functions(body)
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

    def visit_sequence(self, body: list[stmt]) -> list[stmt]:
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
            return super().visit_sequence(body)
        finally:
            self.variants_by_name = prev_variants
            self.specialized_arg_positions_by_base_name = prev_positions

    def visit_Call(self, node: Call) -> Call:
        node = self.generic_visit(node)
        if not isinstance(node.func, Name):
            return node

        # Re-dispatch the call based on the typed argument list instead of the
        # original source name. This lets specialization work after type
        # inference has renamed or nested the functions.
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
