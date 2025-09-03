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


class RemoveDeadCode(CompilingNodeTransformer):
    def __init__(self, arg_types: dict[str, str]):
        self.arg_types = arg_types

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        node.body = self.visit_sequence(node.body)
        return node

    def visit_sequence(self, stmts):
        new_stmts = []
        for stmt in stmts:
            s = self.visit(stmt)
            if isinstance(s, If) and isinstance(s.test, Constant):
                if s.test.value:
                    new_stmts.extend(s.body)
                else:
                    new_stmts.extend(s.orelse)
            else:
                new_stmts.append(s)
        return new_stmts

    def visit_If(self, node: If) -> Any:
        """
        Common types for `ast.If.test`:

            ast.Name      - `if x:`                     (truthiness of a variable)
            ast.Constant  - `if True:`, `if 0:`         (literal truthy/falsy)
            ast.Call      - `if func()`, `isinstance()` (function call)
            ast.Compare   - `if x > 3:`                 (comparison)
            ast.BoolOp    - `if x and y:`               (`and` / `or` logic)
            ast.UnaryOp   - `if not x:`                 (negation, e.g. `not`)
            ast.BinOp     - `if x + y:`                 (binary operation)
            ast.Attribute - `if obj.ready:`             (attribute access)
            ast.Subscript - `if arr[0]:`                (indexing)
            ast.Lambda    - `if lambda x: x > 0:`       (lambda - rare)
            ast.IfExp     - `if a if cond else b:`      (ternary - rare)

            The most likely to be used are ast.Call (if isinstance(...)), ast.BoolOp (if isinstance(...) and/or isinstance(...)), and ast.UnaryOp (if not isinstance(...))
        """
        node.test = self.visit(node.test)
        node.body = self.visit_sequence(node.body)
        node.orelse = self.visit_sequence(node.orelse)
        return node

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

    def visit_BoolOp(self, node: BoolOp) -> Any:
        node.values = [self.visit(v) for v in node.values]
        # Check if all values are constants
        if all(isinstance(v, Constant) for v in node.values):
            values = [bool(v.value) for v in node.values]
            if isinstance(node.op, And):
                return Constant(value=all(values))
            elif isinstance(node.op, Or):
                return Constant(value=any(values))

        # Partial simplification: drop neutral constants
        # e.g. in `x or True`, return Constant(True)
        # e.g. in `x and False`, return Constant(False)
        if isinstance(node.op, And):
            for v in node.values:
                if isinstance(v, Constant) and not v.value:
                    return Constant(value=False)  # short-circuit
            node.values = [
                v for v in node.values if not (isinstance(v, Constant) and v.value)
            ]
        elif isinstance(node.op, Or):
            for v in node.values:
                if isinstance(v, Constant) and v.value:
                    return Constant(value=True)  # short-circuit
            node.values = [
                v for v in node.values if not (isinstance(v, Constant) and not v.value)
            ]
        # If only one value remains, return it directly
        if len(node.values) == 1:
            return node.values[0]
        return node

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        node.operand = self.visit(node.operand)

        # Only handle 'not' operations for now
        if isinstance(node.op, Not):
            # If it's `not <constant>`, simplify it
            if isinstance(node.operand, Constant):
                return Constant(value=not bool(node.operand.value))

        return node

    def visit_IfExp(self, node: IfExp) -> Any:
        node.test = self.visit(node.test)
        node.body = self.visit(node.body)
        node.orelse = self.visit(node.orelse)

        # Simplify if the test condition is a constant
        if isinstance(node.test, Constant):
            if node.test.value:
                return node.body
            else:
                return node.orelse

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
                new_f = RemoveDeadCode(new_arg_types).visit(new_f)
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
