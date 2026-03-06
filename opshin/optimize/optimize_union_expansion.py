from _ast import BoolOp, Call, FunctionDef, If, UnaryOp
from ast import *
from itertools import product
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
                    emitted_stmts = s.body
                else:
                    emitted_stmts = s.orelse
            else:
                emitted_stmts = [s]
            for emitted in emitted_stmts:
                new_stmts.append(emitted)
                if isinstance(emitted, (Return, Raise)):
                    return new_stmts
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

    class _RewriteExpandedCalls(NodeTransformer):
        def __init__(
            self,
            union_arg_positions: dict[str, list[int]],
            known_var_types: dict[str, str],
        ):
            self.union_arg_positions = union_arg_positions
            self.known_var_types = known_var_types

        def _known_type_suffix(self, node: expr) -> str:
            if isinstance(node, Name):
                return self.known_var_types.get(node.id)
            return None

        def visit_Call(self, node: Call):
            node = self.generic_visit(node)
            if not isinstance(node.func, Name):
                return node
            base_name = node.func.id
            if base_name not in self.union_arg_positions:
                return node
            suffixes = []
            for arg_pos in self.union_arg_positions[base_name]:
                if arg_pos >= len(node.args):
                    return node
                suffix = self._known_type_suffix(node.args[arg_pos])
                if suffix is None:
                    return node
                suffixes.append(suffix)
            node.func.id = base_name + "+" + "".join(f"_{s}" for s in suffixes)
            return node

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

    def _arg_type_suffixes(self, stmt: FunctionDef) -> dict[str, str]:
        known_types = {}
        for arg in stmt.args.args:
            if arg.annotation is None:
                continue
            if self.is_Union_annotation(arg.annotation):
                continue
            known_types[arg.arg] = getattr(arg.annotation, "id", type_to_suffix(arg.annotation))
        return known_types

    def _union_arg_positions(self, stmt: FunctionDef) -> list[int]:
        positions = []
        for i, arg in enumerate(stmt.args.args):
            if self.is_Union_annotation(arg.annotation):
                positions.append(i)
        return positions

    def _specialized_name(self, base_name: str, suffixes: list[str]) -> str:
        return base_name + "+" + "".join(f"_{s}" for s in suffixes)

    def _expanded_dispatch_call(
        self, base_name: str, suffixes: list[str], args: list[arg]
    ) -> Return:
        return Return(
            value=Call(
                func=Name(id=self._specialized_name(base_name, suffixes), ctx=Load()),
                args=[Name(id=a.arg, ctx=Load()) for a in args],
                keywords=[],
            )
        )

    def _build_dispatch_tree(
        self,
        stmt: FunctionDef,
        union_positions: list[int],
        union_type_options: list[list[expr]],
        depth: int,
        chosen_suffixes: list[str],
    ) -> list[stmt]:
        if depth >= len(union_positions):
            return [
                self._expanded_dispatch_call(
                    stmt.name,
                    chosen_suffixes,
                    stmt.args.args,
                )
            ]

        arg_idx = union_positions[depth]
        arg_name = stmt.args.args[arg_idx].arg
        options = union_type_options[depth]

        def build_option_chain(option_index: int) -> list[stmt]:
            typ = options[option_index]
            typ_suffix = getattr(typ, "id", type_to_suffix(typ))
            branch_body = self._build_dispatch_tree(
                stmt,
                union_positions,
                union_type_options,
                depth + 1,
                [*chosen_suffixes, typ_suffix],
            )
            if option_index == len(options) - 1:
                return branch_body
            return [
                If(
                    test=Call(
                        func=Name(id="isinstance", ctx=Load()),
                        args=[Name(id=arg_name, ctx=Load()), deepcopy(typ)],
                        keywords=[],
                    ),
                    body=branch_body,
                    orelse=build_option_chain(option_index + 1),
                )
            ]

        return build_option_chain(0)

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
            new_f.name = self._specialized_name(stmt.name, suffixes)
            if new_f.name in seen_names:
                continue
            seen_names.add(new_f.name)
            new_f = RemoveDeadCode(known_union_types).visit(new_f)
            new_functions.append(new_f)
        return new_functions

    def visit_sequence(self, body):
        union_arg_positions: dict[str, list[int]] = {}
        for stmt in body:
            if not isinstance(stmt, FunctionDef):
                continue
            positions = self._union_arg_positions(stmt)
            if positions:
                union_arg_positions[stmt.name] = positions
        self.union_arg_positions = union_arg_positions

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
            stmt.body = self._build_dispatch_tree(
                stmt, union_positions, union_type_options, 0, []
            )
            new_body.append(stmt)
            new_body.extend(new_funcs)

        for stmt in new_body:
            if not isinstance(stmt, FunctionDef):
                continue
            known_var_types = self._arg_type_suffixes(stmt)
            rewriter = self._RewriteExpandedCalls(
                self.union_arg_positions, known_var_types
            )
            stmt.body = [rewriter.visit(s) for s in stmt.body]
        return new_body
