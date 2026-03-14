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

    def _mentioned_in_statement(self, statement: stmt, name: str) -> bool:
        return any(
            isinstance(child, Name) and child.id == name for child in walk(statement)
        )

    def _mentioned_later(self, statements: list[stmt], name: str) -> bool:
        return any(
            self._mentioned_in_statement(statement, name) for statement in statements
        )

    def _load_count(self, expression: expr, name: str) -> int:
        return sum(
            1
            for child in walk(expression)
            if isinstance(child, Name)
            and isinstance(child.ctx, Load)
            and child.id == name
        )

    def _guaranteed_load_count(self, expression: expr, name: str) -> int:
        if isinstance(expression, Name):
            return int(isinstance(expression.ctx, Load) and expression.id == name)
        if isinstance(expression, BoolOp):
            return self._guaranteed_load_count(expression.values[0], name)
        if isinstance(expression, IfExp):
            return self._guaranteed_load_count(expression.test, name)
        if isinstance(expression, Compare):
            count = self._guaranteed_load_count(expression.left, name)
            if expression.comparators:
                count += self._guaranteed_load_count(expression.comparators[0], name)
            return count
        if isinstance(expression, Lambda):
            return 0
        return sum(
            self._guaranteed_load_count(child, name)
            for child in iter_child_nodes(expression)
            if isinstance(child, AST)
        )

    def _loaded_names(self, expression: expr) -> set[str]:
        return {
            child.id
            for child in walk(expression)
            if isinstance(child, Name) and isinstance(child.ctx, Load)
        }

    def _stored_names(self, statement: stmt) -> set[str]:
        return {
            child.id
            for child in walk(statement)
            if isinstance(child, Name) and isinstance(child.ctx, Store)
        }

    def _dependencies_reassigned(
        self, statements: list[stmt], expression: expr, assigned_name: str
    ) -> bool:
        dependencies = self._loaded_names(expression) - {assigned_name}
        return any(self._stored_names(statement) & dependencies for statement in statements)

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
        if use_expr is None:
            return None
        if (
            self._load_count(use_expr, assigned_name) != 1
            or self._guaranteed_load_count(use_expr, assigned_name) != 1
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

        rewritten = []
        index = 0
        while index < len(statements):
            statement = statements[index]
            if (
                isinstance(statement, Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], Name)
            ):
                assigned_name = statement.targets[0].id
                use_index = None
                for candidate_index in range(index + 1, len(statements)):
                    if self._mentioned_in_statement(
                        statements[candidate_index], assigned_name
                    ):
                        use_index = candidate_index
                        break
                if (
                    use_index is not None
                    and not self._mentioned_later(
                        statements[use_index + 1 :], assigned_name
                    )
                ):
                    between = statements[index + 1 : use_index]
                    if not self._dependencies_reassigned(
                        between, statement.value, assigned_name
                    ):
                        inlined = self._inline_pair(
                            statement,
                            statements[use_index],
                        )
                        if inlined is not None:
                            rewritten.extend(statements[index + 1 : use_index])
                            rewritten.append(inlined)
                            index = use_index + 1
                            continue
            rewritten.append(statements[index])
            index += 1
        return rewritten

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
