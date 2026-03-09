from _ast import Call, FunctionDef
from ast import *
from itertools import product
from typing import Any, List, Optional
from ..util import CompilingNodeTransformer
from .optimize_remove_deadconds import OptimizeRemoveDeadConditions
from copy import deepcopy

"""
Expand union types
"""


UNION_SPECIALIZATION_SEPARATOR = "+"


def _sanitize_type_suffix(raw: str) -> str:
    return (
        raw.replace(" ", "")
        .replace("__", "___")
        .replace("[", "_l_")
        .replace("]", "_r_")
        .replace(",", "_c_")
        .replace(".", "_d_")
    )


def type_to_suffix(typ: expr) -> str:
    try:
        raw = unparse(typ)
    except Exception:
        return "UnknownType"
    return _sanitize_type_suffix(raw)


def type_to_specialization_suffix(typ: Any) -> str:
    if isinstance(typ, expr):
        if isinstance(typ, Name):
            return _sanitize_type_suffix(typ.id)
        return type_to_suffix(typ)

    concrete_typ = getattr(typ, "typ", typ)
    if hasattr(concrete_typ, "record") and hasattr(concrete_typ.record, "orig_name"):
        return _sanitize_type_suffix(concrete_typ.record.orig_name)
    if hasattr(concrete_typ, "python_type"):
        return _sanitize_type_suffix(concrete_typ.python_type())
    return _sanitize_type_suffix(str(concrete_typ))


def get_specialized_function_name_from_suffixes(
    base_name: str, suffixes: list[str]
) -> str:
    base_name_no_scope, scope_suffix = base_name, None
    if "_" in base_name:
        candidate_base, candidate_scope = base_name.rsplit("_", 1)
        if candidate_scope.isdigit():
            base_name_no_scope, scope_suffix = candidate_base, candidate_scope

    specialized_name = (
        base_name_no_scope
        + UNION_SPECIALIZATION_SEPARATOR
        + "".join(f"_{suffix}" for suffix in suffixes)
    )
    if scope_suffix is not None:
        return f"{specialized_name}_{scope_suffix}"
    return specialized_name


def get_specialized_function_name_for_types(
    base_name: str,
    argument_types: list[Any],
    specialized_argument_positions: Optional[list[int]] = None,
) -> str:
    if specialized_argument_positions is None:
        specialized_argument_positions = list(range(len(argument_types)))
    selected_types = [argument_types[i] for i in specialized_argument_positions]
    suffixes = [type_to_specialization_suffix(t) for t in selected_types]
    return get_specialized_function_name_from_suffixes(base_name, suffixes)


def split_specialized_function_name(
    function_name: str,
) -> Optional[tuple[str, str]]:
    if UNION_SPECIALIZATION_SEPARATOR not in function_name:
        return None
    return function_name.split(UNION_SPECIALIZATION_SEPARATOR, 1)


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
                    typ_str = getattr(typ, "id", type_to_suffix(typ))
                    return Constant(value=(known_type == typ_str))

        return node


class OptimizeUnionExpansion(CompilingNodeTransformer):
    step = "Expanding Unions"

    def visit(self, node):
        if hasattr(node, "body") and isinstance(node.body, list):
            node.body = self.visit_sequence(node.body)
        if hasattr(node, "orelse") and isinstance(node.orelse, list):
            node.orelse = self.visit_sequence(node.orelse)
        if hasattr(node, "finalbody") and isinstance(node.finalbody, list):
            node.finalbody = self.visit_sequence(node.finalbody)
        return super().visit(node)

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
    ) -> List[FunctionDef]:
        new_functions = []
        seen_names = set()
        for concrete_types in product(*union_type_options):
            new_f = deepcopy(stmt)
            suffixes = []
            known_union_types = {}
            for i, typ in zip(union_positions, concrete_types):
                concrete_type = deepcopy(typ)
                new_f.args.args[i].annotation = concrete_type
                typ_suffix = getattr(concrete_type, "id", type_to_suffix(concrete_type))
                suffixes.append(typ_suffix)
                known_union_types[new_f.args.args[i].arg] = typ_suffix
            new_f.name = get_specialized_function_name_from_suffixes(
                stmt.name, suffixes
            )
            if new_f.name in seen_names:
                continue
            seen_names.add(new_f.name)
            new_f = RewriteKnownIsinstanceChecks(known_union_types).visit(new_f)
            new_f = OptimizeRemoveDeadConditions().visit(new_f)
            new_functions.append(new_f)
        return new_functions

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
            new_funcs = self._specialize_function(
                stmt, union_positions, union_type_options
            )
            stmt.expanded_variants = [f.name for f in new_funcs]
            new_body.append(stmt)
            new_body.extend(new_funcs)
        return new_body
