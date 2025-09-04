from _ast import BoolOp, Call, FunctionDef, If, UnaryOp
from ast import *
from typing import Any, List
from ..util import CompilingNodeTransformer
from copy import deepcopy

"""
Expand union types
"""


def type_to_suffix(typ: expr) -> str:
    try:
        raw = unparse(typ)
    except Exception:
        return "UnknownType"
    return (
        raw.replace(" ", "")
        .replace("__", "___")
        .replace("[", "_l_")
        .replace("]", "_r_")
        .replace(",", "_c_")
        .replace(".", "_d_")
    )


class SimplifyIsInstance(CompilingNodeTransformer):
    def __init__(self, arg_types: dict[str, str]):
        self.arg_types = arg_types

    def visit_Call(self, node: Call) -> Any:
        node = self.generic_visit(node)
        # Check if this is an isinstance(x, T) call
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

    def split_functions(
        self, stmt: FunctionDef, args: list, arg_types: dict, naming=""
    ) -> List[FunctionDef]:
        """
                Recursively generate variants of a function with all possible combinations
        of expanded union types for its arguments.
        """
        new_functions = []
        for i, arg in enumerate(args):
            if not arg:
                continue
            n_args = deepcopy(args)
            n_args[i] = False
            for typ in arg:
                new_f = deepcopy(stmt)
                new_f.args.args[i].annotation = typ
                typ_str = getattr(typ, "id", type_to_suffix(typ))
                new_f.name = f"{naming}_{typ_str}"
                new_arg_types = deepcopy(arg_types)
                new_arg_types[stmt.args.args[i].arg] = typ_str
                new_f = SimplifyIsInstance(new_arg_types).visit(new_f)
                new_functions.append(new_f)
                new_functions.extend(
                    self.split_functions(new_f, n_args, new_arg_types, new_f.name)
                )
            # Look for variation where this arg is still Union
            new_functions.extend(
                self.split_functions(stmt, n_args, arg_types, f"{naming}_Union")
            )
            # Handle only one Union per recursion level
            break

        return new_functions

    def visit_sequence(self, body):
        new_body = []
        for stmt in body:
            new_body.append(stmt)
            if isinstance(stmt, FunctionDef):
                args = [
                    self.is_Union_annotation(arg.annotation) for arg in stmt.args.args
                ]
                # number prefix here should guarantee naming uniqueness
                new_funcs = self.split_functions(stmt, args, {}, stmt.name + "+")
                # track variants
                new_body[-1].expanded_variants = [f.name for f in new_funcs]
                new_body.extend(new_funcs)
        return new_body
