from _ast import Call, FunctionDef
from ast import *
from dataclasses import dataclass, field
from itertools import product
from typing import Any, List, Optional
from ..util import CompilingNodeTransformer, NameSupply
from .optimize_remove_deadconds import OptimizeRemoveDeadConditions
from copy import deepcopy

"""
Expand union types
"""


def _sanitize_type_key(raw: str) -> str:
    return (
        raw.replace(" ", "")
        .replace("__", "___")
        .replace("[", "_l_")
        .replace("]", "_r_")
        .replace(",", "_c_")
        .replace(".", "_d_")
    )


def type_to_key(typ: expr) -> str:
    try:
        raw = unparse(typ)
    except Exception:
        return "UnknownType"
    return _sanitize_type_key(raw)


def type_to_specialization_key(typ: Any) -> str:
    if isinstance(typ, expr):
        if isinstance(typ, Name):
            return _sanitize_type_key(typ.id)
        return type_to_key(typ)

    concrete_typ = getattr(typ, "typ", typ)
    if hasattr(concrete_typ, "record") and hasattr(concrete_typ.record, "orig_name"):
        return _sanitize_type_key(concrete_typ.record.orig_name)
    if hasattr(concrete_typ, "python_type"):
        return _sanitize_type_key(concrete_typ.python_type())
    return _sanitize_type_key(str(concrete_typ))


@dataclass(frozen=True)
class UnionExpansionVariant:
    id: str


@dataclass
class UnionExpansion:
    specialized_argument_positions: tuple[int, ...]
    variants: dict[tuple[str, ...], UnionExpansionVariant] = field(default_factory=dict)

    @staticmethod
    def _type_key(argument_types: list[Any]) -> tuple[str, ...]:
        return tuple(type_to_specialization_key(typ) for typ in argument_types)

    def register(
        self,
        specialized_argument_types: list[Any],
        variant: UnionExpansionVariant,
    ) -> bool:
        key = self._type_key(specialized_argument_types)
        if key in self.variants:
            return False
        self.variants[key] = variant
        return True

    def variant_for(self, argument_types: list[Any]) -> Optional[UnionExpansionVariant]:
        specialized_types = [
            argument_types[i] for i in self.specialized_argument_positions
        ]
        return self.variants.get(self._type_key(specialized_types))


class RewriteKnownIsinstanceChecks(CompilingNodeTransformer):
    def __init__(self, arg_types: dict[str, str]):
        self.arg_types = arg_types

    def visit_Call(self, node: Call) -> Any:
        node = self.generic_visit(node)
        if (
            isinstance(node.func, Name)
            and node.func.id == "isinstance"
            and len(node.args) == 2
        ):
            arg, typ = node.args
            if isinstance(arg, Name) and isinstance(typ, Name):
                known_type = self.arg_types.get(arg.id)
                if known_type is not None:
                    typ_str = getattr(typ, "id", type_to_key(typ))
                    return Constant(value=(known_type == typ_str))

        return node


class OptimizeUnionExpansion(CompilingNodeTransformer):
    step = "Expanding Unions"

    def __init__(self):
        self.current_class_name: Optional[str] = None

    def visit(self, node):
        previous_class_name = self.current_class_name
        if isinstance(node, ClassDef):
            self.current_class_name = node.name
        try:
            if isinstance(node, Module):
                self.name_supply = NameSupply.from_tree(node, "union")
            if hasattr(node, "body") and isinstance(node.body, list):
                node.body = self.visit_sequence(node.body)
            if hasattr(node, "orelse") and isinstance(node.orelse, list):
                node.orelse = self.visit_sequence(node.orelse)
            if hasattr(node, "finalbody") and isinstance(node.finalbody, list):
                node.finalbody = self.visit_sequence(node.finalbody)
            return super().visit(node)
        finally:
            self.current_class_name = previous_class_name

    def specialization_key(self, typ: expr) -> str:
        if (
            isinstance(typ, Name)
            and typ.id == "Self"
            and self.current_class_name is not None
        ):
            return _sanitize_type_key(self.current_class_name)
        if isinstance(typ, Constant) and isinstance(typ.value, str):
            return _sanitize_type_key(typ.value)
        return type_to_specialization_key(typ)

    def is_Union_annotation(self, ann: expr):
        if isinstance(ann, Subscript) and isinstance(ann.value, Name):
            if ann.value.id == "Union":
                return ann.slice.elts
        return False

    def _union_arg_positions(self, stmt: FunctionDef) -> list[int]:
        positions = []
        for i, arg in enumerate(stmt.args.args):
            if self.is_Union_annotation(arg.annotation):
                positions.append(i)
        return positions

    def _specialize_function(
        self,
        stmt: FunctionDef,
        union_positions: list[int],
        union_type_options: list[list[expr]],
    ) -> tuple[List[FunctionDef], UnionExpansion]:
        new_functions = []
        expansion = UnionExpansion(tuple(union_positions))
        for concrete_types in product(*union_type_options):
            new_f = deepcopy(stmt)
            # Calls are first type-checked against the unspecialized function,
            # which supplies omitted defaults. Specialized variants are an
            # internal dispatch target and must not independently re-check a
            # default against every narrowed union member.
            new_f.args.defaults = []
            known_union_types = {}
            specialization_keys = []
            for i, typ in zip(union_positions, concrete_types):
                concrete_type = deepcopy(typ)
                new_f.args.args[i].annotation = concrete_type
                type_key = self.specialization_key(concrete_type)
                known_union_types[new_f.args.args[i].arg] = type_key
                specialization_keys.append(type_key)
            variant = UnionExpansionVariant(self.name_supply.fresh_name())
            if not expansion.register(specialization_keys, variant):
                continue
            new_f.name = variant.id
            new_f.union_expansion_variant = variant
            new_f = RewriteKnownIsinstanceChecks(known_union_types).visit(new_f)
            new_f = OptimizeRemoveDeadConditions().visit(new_f)
            new_functions.append(new_f)
        return new_functions, expansion

    def visit_sequence(self, body):
        new_body = []
        for stmt in body:
            if not isinstance(stmt, FunctionDef):
                new_body.append(stmt)
                continue

            union_positions = self._union_arg_positions(stmt)
            if not union_positions:
                new_body.append(stmt)
                continue

            union_type_options = [
                self.is_Union_annotation(stmt.args.args[i].annotation)
                for i in union_positions
            ]
            new_funcs, expansion = self._specialize_function(
                stmt, union_positions, union_type_options
            )
            stmt.union_expansion = expansion
            new_body.append(stmt)
            new_body.extend(new_funcs)
        return new_body
