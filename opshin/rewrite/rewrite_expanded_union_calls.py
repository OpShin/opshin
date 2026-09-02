from ast import *
from dataclasses import dataclass

from ..type_impls import InstanceType
from ..typed_util import (
    ScopedSequenceNodeTransformer,
    collect_typed_functions,
)
from ..optimize.optimize_union_expansion import (
    UnionExpansion,
    UnionExpansionVariant,
)


@dataclass(frozen=True)
class _ExpandedVariant:
    name: str
    typ: InstanceType


@dataclass(frozen=True)
class _ExpandedFunction:
    expansion: UnionExpansion
    variants: dict[UnionExpansionVariant, _ExpandedVariant]


class RewriteExpandedUnionCalls(ScopedSequenceNodeTransformer):
    # This pass keeps track of specialized union variants in the current nested
    # statement sequence, so calls can be rewritten even when the expanded
    # functions live inside another function or control-flow block.
    step = "Rewriting expanded union calls"

    def __init__(self):
        super().__init__()
        self.expanded_functions_by_name = {}

    def _collect_expanded_variants(self, body: list[stmt]):
        typed_functions = collect_typed_functions(body)
        variants_by_id = {}
        for function in typed_functions:
            variant_id = getattr(function, "union_expansion_variant", None)
            if variant_id is None:
                continue
            variants_by_id[variant_id] = _ExpandedVariant(
                name=function.name,
                typ=function.typ,
            )

        expanded_functions_by_name = {}
        for function in typed_functions:
            expansion = getattr(function, "union_expansion", None)
            if expansion is None:
                continue
            expanded_functions_by_name[function.name] = _ExpandedFunction(
                expansion=expansion,
                variants={
                    variant_id: variants_by_id[variant_id]
                    for variant_id in expansion.variants.values()
                    if variant_id in variants_by_id
                },
            )

        return expanded_functions_by_name

    def visit_sequence(self, body: list[stmt]) -> list[stmt]:
        previous = dict(self.expanded_functions_by_name)
        self.expanded_functions_by_name.update(self._collect_expanded_variants(body))
        try:
            return super().visit_sequence(body)
        finally:
            self.expanded_functions_by_name = previous

    def visit_Call(self, node: Call) -> Call:
        node = self.generic_visit(node)
        if not isinstance(node.func, Name):
            return node

        # Re-dispatch the call based on the typed argument list instead of the
        # original source name. This lets specialization work after type
        # inference has renamed or nested the functions.
        expanded_function = self.expanded_functions_by_name.get(node.func.id)
        if expanded_function is None:
            return node

        variant_id = expanded_function.expansion.variant_for(
            [arg.typ for arg in node.args]
        )
        variant = expanded_function.variants.get(variant_id)
        if variant is None:
            return node

        argtyps = variant.typ.typ.argtyps
        if len(node.args) != len(argtyps):
            return node
        if any(actual.typ != expected for actual, expected in zip(node.args, argtyps)):
            return node

        node.func.id = variant.name
        node.func.typ = variant.typ
        # Specialized variants have no defaults of their own: omitted defaults
        # were already materialized while checking the unspecialized call.
        node.provided_arg_indices = list(range(len(node.args)))
        return node
