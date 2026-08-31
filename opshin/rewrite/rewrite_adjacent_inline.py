import ast
from bisect import bisect_right
from collections import defaultdict
from copy import copy

from ..typed_util import ScopedSequenceNodeTransformer
from ..util import CompilingNodeTransformer


class _ExpressionNameSubstitutor(CompilingNodeTransformer):
    step = "Inlining adjacent expression"

    def __init__(self, name: str, replacement: ast.expr):
        self.name = name
        self.replacement = replacement

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load) and node.id == self.name:
            replacement = copy(self.replacement)
            ast.copy_location(replacement, node)
            return replacement
        return node


class RewriteAdjacentInline(ScopedSequenceNodeTransformer):
    step = "Inlining adjacent single-use expressions"

    def _load_count(self, expression: ast.expr, name: str) -> int:
        return sum(
            1
            for child in ast.walk(expression)
            if isinstance(child, ast.Name)
            and isinstance(child.ctx, ast.Load)
            and child.id == name
        )

    def _guaranteed_load_count(self, expression: ast.expr, name: str) -> int:
        if isinstance(expression, ast.Name):
            return int(isinstance(expression.ctx, ast.Load) and expression.id == name)
        if isinstance(expression, ast.BoolOp):
            return self._guaranteed_load_count(expression.values[0], name)
        if isinstance(expression, ast.IfExp):
            return self._guaranteed_load_count(expression.test, name)
        if isinstance(expression, ast.Compare):
            count = self._guaranteed_load_count(expression.left, name)
            if expression.comparators:
                count += self._guaranteed_load_count(expression.comparators[0], name)
            return count
        if isinstance(
            expression,
            (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
        ):
            return 0
        return sum(
            self._guaranteed_load_count(child, name)
            for child in ast.iter_child_nodes(expression)
            if isinstance(child, ast.expr)
        )

    def _loaded_names(self, expression: ast.expr) -> set[str]:
        return {
            child.id
            for child in ast.walk(expression)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
        }

    def _stored_names(self, statement: ast.stmt) -> set[str]:
        return {
            child.id
            for child in ast.walk(statement)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
        }

    def _statement_names(self, statement: ast.stmt) -> set[str]:
        return {
            child.id for child in ast.walk(statement) if isinstance(child, ast.Name)
        }

    def _is_straight_line_statement(self, statement: ast.stmt) -> bool:
        return isinstance(
            statement, (ast.Assign, ast.AnnAssign, ast.Expr, ast.Pass, ast.Assert)
        )

    def _extract_expression(self, node: ast.stmt):
        if isinstance(node, ast.Return) and node.value is not None:
            return node.value, "value"
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            return node.value, "value"
        if isinstance(node, ast.AnnAssign) and node.value is not None:
            return node.value, "value"
        if isinstance(node, ast.Expr):
            return node.value, "value"
        return None, None

    def _inline_pair(self, assignment: ast.stmt, use_statement: ast.stmt):
        if not (
            isinstance(assignment, ast.Assign)
            and len(assignment.targets) == 1
            and isinstance(assignment.targets[0], ast.Name)
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

    def visit_sequence(self, body: list[ast.stmt]) -> list[ast.stmt]:
        statements = super().visit_sequence(body)
        mentioned_by_index = [
            self._statement_names(statement) for statement in statements
        ]
        stored_by_index = [self._stored_names(statement) for statement in statements]
        mention_indices = defaultdict(set)
        store_indices = defaultdict(set)
        for index in range(len(statements)):
            for name in mentioned_by_index[index]:
                mention_indices[name].add(index)
            for name in stored_by_index[index]:
                store_indices[name].add(index)
        control_flow_indices = [
            index
            for index, statement in enumerate(statements)
            if not self._is_straight_line_statement(statement)
        ]

        def replace_statement(index: int, statement):
            for name in mentioned_by_index[index]:
                mention_indices[name].remove(index)
            for name in stored_by_index[index]:
                store_indices[name].remove(index)
            statements[index] = statement
            mentioned_by_index[index] = (
                self._statement_names(statement) if statement is not None else set()
            )
            stored_by_index[index] = (
                self._stored_names(statement) if statement is not None else set()
            )
            for name in mentioned_by_index[index]:
                mention_indices[name].add(index)
            for name in stored_by_index[index]:
                store_indices[name].add(index)

        for index in range(len(statements) - 1, -1, -1):
            statement = statements[index]
            if not (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
            ):
                continue

            assigned_name = statement.targets[0].id
            use_indices = [
                use_index
                for use_index in mention_indices[assigned_name]
                if use_index > index
            ]
            if len(use_indices) != 1:
                continue
            use_index = use_indices[0]
            first_control_flow = bisect_right(control_flow_indices, index)
            if (
                first_control_flow < len(control_flow_indices)
                and control_flow_indices[first_control_flow] < use_index
            ):
                continue
            dependencies = self._loaded_names(statement.value) - {assigned_name}
            if any(
                index < store_index < use_index
                for dependency in dependencies
                for store_index in store_indices[dependency]
            ):
                continue
            inlined = self._inline_pair(statement, statements[use_index])
            if inlined is None:
                continue
            replace_statement(use_index, inlined)
            replace_statement(index, None)

        return [statement for statement in statements if statement is not None]

    def visit_While(self, node: ast.While):
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        node_cp.body = list(node.body)
        node_cp.orelse = list(node.orelse)
        return node_cp

    def visit_For(self, node: ast.For):
        node_cp = copy(node)
        node_cp.target = self.visit(node.target)
        node_cp.iter = self.visit(node.iter)
        node_cp.body = list(node.body)
        node_cp.orelse = list(node.orelse)
        return node_cp
