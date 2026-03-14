from ast import *
from copy import copy

from ..typed_util import ScopedSequenceNodeTransformer
from ..util import CompilingNodeTransformer


class _ExpressionNameSubstitutor(CompilingNodeTransformer):
    step = "Inlining adjacent expression"

    def __init__(self, name: str, replacement: expr):
        self.name = name
        self.replacement = replacement

    def visit_Name(self, node: Name):
        if isinstance(node.ctx, Load) and node.id == self.name:
            replacement = copy(self.replacement)
            copy_location(replacement, node)
            return replacement
        return node


class RewriteAdjacentInline(ScopedSequenceNodeTransformer):
    step = "Inlining adjacent single-use expressions"

    def _mentioned_later(self, statements: list[stmt], name: str) -> bool:
        return any(
            isinstance(child, Name) and child.id == name
            for statement in statements
            for child in walk(statement)
        )

    def _extract_expression(self, node: stmt):
        if isinstance(node, Return) and node.value is not None:
            return node.value, "value"
        if isinstance(node, Assign) and len(node.targets) == 1:
            return node.value, "value"
        if isinstance(node, AnnAssign) and node.value is not None:
            return node.value, "value"
        if isinstance(node, Expr):
            return node.value, "value"
        return None, None

    def _inline_pair(self, assignment: stmt, use_statement: stmt):
        if not (
            isinstance(assignment, Assign)
            and len(assignment.targets) == 1
            and isinstance(assignment.targets[0], Name)
        ):
            return None

        assigned_name = assignment.targets[0].id
        use_expr, field_name = self._extract_expression(use_statement)
        if not (
            isinstance(use_expr, Name)
            and isinstance(use_expr.ctx, Load)
            and use_expr.id == assigned_name
        ):
            return None

        rewritten_statement = copy(use_statement)
        rewritten_expr = _ExpressionNameSubstitutor(
            assigned_name, assignment.value
        ).visit(copy(use_expr))
        setattr(rewritten_statement, field_name, rewritten_expr)
        return rewritten_statement

    def visit_sequence(self, body: list[stmt]) -> list[stmt]:
        statements = super().visit_sequence(body)

        while True:
            rewritten = []
            changed = False
            index = 0
            while index < len(statements):
                if index + 1 < len(statements):
                    assigned_name = None
                    if (
                        isinstance(statements[index], Assign)
                        and len(statements[index].targets) == 1
                        and isinstance(statements[index].targets[0], Name)
                    ):
                        assigned_name = statements[index].targets[0].id
                    inlined = (
                        None
                        if assigned_name is not None
                        and self._mentioned_later(statements[index + 2 :], assigned_name)
                        else self._inline_pair(statements[index], statements[index + 1])
                    )
                    if inlined is not None:
                        rewritten.append(inlined)
                        index += 2
                        changed = True
                        continue
                rewritten.append(statements[index])
                index += 1
            statements = rewritten
            if not changed:
                return statements

    def visit_While(self, node: While):
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = list(node.body)
        node_cp.orelse = list(node.orelse)
        return node_cp

    def visit_For(self, node: For):
        node_cp = copy(node)
        node_cp.target = self.visit(node.target)
        node_cp.iter = self.visit(node.iter)
        node_cp.body = list(node.body)
        node_cp.orelse = list(node.orelse)
        return node_cp
