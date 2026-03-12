import ast
import re
from copy import copy

from ..typed_util import FlatteningScopedSequenceNodeTransformer


SSA_SUFFIX_RE = re.compile(r"_v\d+$")


def strip_ssa_suffix(name: str) -> str:
    return SSA_SUFFIX_RE.sub("", name)


class RewriteSSA(FlatteningScopedSequenceNodeTransformer):
    step = "Rewriting scoped variables into SSA-like versions"

    def __init__(self):
        self._env_stack = []
        self._version_counters = {}
        self._pinned_stack = [set()]
        self._protected_stack = [set()]

    def _current_env(self) -> dict[str, str]:
        return self._env_stack[-1]

    def _current_pinned(self) -> set[str]:
        return self._pinned_stack[-1]

    def _current_protected(self) -> set[str]:
        return self._protected_stack[-1]

    def _push_env(self, env: dict[str, str] | None = None):
        self._env_stack.append(dict(env or {}))

    def _pop_env(self) -> dict[str, str]:
        return self._env_stack.pop()

    def _fresh_name(self, base_name: str) -> str:
        version = self._version_counters.get(base_name, 0) + 1
        self._version_counters[base_name] = version
        return f"{base_name}_v{version}"

    def _lookup_name(self, name: str) -> str:
        base_name = strip_ssa_suffix(name)
        return self._current_env().get(base_name, base_name)

    def _set_current_name(self, base_name: str, name: str):
        self._current_env()[base_name] = name

    def _orig_name(self, node: ast.AST, fallback: str) -> str:
        return getattr(node, "orig_id", getattr(node, "orig_arg", fallback))

    def _make_name(self, name: str, ctx: ast.expr_context, orig_id: str) -> ast.Name:
        node = ast.Name(id=name, ctx=ctx)
        node.orig_id = orig_id
        return node

    def _make_assign(
        self, target_name: str, source_name: str, orig_id: str
    ) -> ast.Assign:
        return ast.Assign(
            targets=[self._make_name(target_name, ast.Store(), orig_id)],
            value=self._make_name(source_name, ast.Load(), orig_id),
        )

    def _branch_join_names(
        self,
        initial_env: dict[str, str],
        body_env: dict[str, str],
        else_env: dict[str, str],
    ) -> dict[str, str]:
        all_names = set(initial_env) | set(body_env) | set(else_env)
        joined_env = dict(initial_env)
        for base_name in sorted(all_names):
            body_name = body_env.get(base_name, initial_env.get(base_name, base_name))
            else_name = else_env.get(base_name, initial_env.get(base_name, base_name))
            if base_name in self._current_protected():
                joined_env[base_name] = initial_env.get(base_name, base_name)
                continue
            if body_name == else_name:
                joined_env[base_name] = body_name
                continue
            joined_env[base_name] = self._fresh_name(base_name)
        return joined_env

    def _append_branch_joins(
        self,
        branch: list[ast.stmt],
        branch_env: dict[str, str],
        joined_env: dict[str, str],
    ) -> list[ast.stmt]:
        updated_branch = list(branch)
        for base_name, joined_name in joined_env.items():
            branch_name = branch_env.get(base_name, joined_name)
            if branch_name == joined_name:
                continue
            updated_branch.append(
                self._make_assign(
                    joined_name, branch_name, self._orig_name_value(base_name)
                )
            )
        return updated_branch

    def _orig_name_value(self, name: str) -> str:
        name = strip_ssa_suffix(name)
        while re.search(r"_\d+$", name):
            name = re.sub(r"_\d+$", "", name)
        return name

    def _written_bases(self, node: ast.AST) -> set[str]:
        names = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                names.add(strip_ssa_suffix(child.id))
        return names

    def _pin_bases(self, bases: set[str]):
        self._pinned_stack.append(self._current_pinned() | set(bases))

    def _unpin_bases(self):
        self._pinned_stack.pop()

    def _push_protected(self, bases: set[str]):
        self._protected_stack.append(set(bases))

    def _pop_protected(self):
        self._protected_stack.pop()

    def _in_module_scope(self) -> bool:
        return len(self._env_stack) == 1

    def _walk_scope_statements(self, statements, on_name=None, on_function=None):
        for stmt in statements:
            if isinstance(stmt, ast.FunctionDef):
                if on_function is not None:
                    on_function(stmt)
                continue
            if isinstance(stmt, ast.ClassDef):
                for class_stmt in stmt.body:
                    if (
                        isinstance(class_stmt, ast.FunctionDef)
                        and on_function is not None
                    ):
                        on_function(class_stmt)
                continue
            for child in ast.iter_child_nodes(stmt):
                if isinstance(child, ast.stmt):
                    continue
                for grandchild in ast.walk(child):
                    if isinstance(grandchild, ast.Name) and on_name is not None:
                        on_name(grandchild)
            for field in ("body", "orelse", "finalbody"):
                nested = getattr(stmt, field, None)
                if isinstance(nested, list):
                    self._walk_scope_statements(nested, on_name, on_function)

    def _bound_bases_in_scope(self, node: ast.FunctionDef) -> set[str]:
        bound = {strip_ssa_suffix(arg.arg) for arg in node.args.args}

        def record_name(name: ast.Name):
            if isinstance(name.ctx, ast.Store):
                bound.add(strip_ssa_suffix(name.id))

        def record_function(fn: ast.FunctionDef):
            bound.add(strip_ssa_suffix(fn.name))

        self._walk_scope_statements(node.body, record_name, record_function)
        return bound

    def _loaded_bases_in_scope(self, node: ast.FunctionDef) -> set[str]:
        loaded = set()

        def record_name(name: ast.Name):
            if isinstance(name.ctx, ast.Load):
                loaded.add(strip_ssa_suffix(name.id))

        self._walk_scope_statements(node.body, record_name, None)
        return loaded

    def _nested_function_defs(self, node: ast.FunctionDef) -> list[ast.FunctionDef]:
        nested = []
        self._walk_scope_statements(node.body, None, nested.append)
        return nested

    def _captured_bases_in_function(self, node: ast.FunctionDef) -> set[str]:
        current_bound = self._bound_bases_in_scope(node)
        captured = set()

        def collect_from_nested(function: ast.FunctionDef, shadowed: set[str]):
            local_bound = self._bound_bases_in_scope(function)
            local_loaded = self._loaded_bases_in_scope(function)
            for base_name in local_loaded:
                if (
                    base_name in current_bound
                    and base_name not in shadowed
                    and base_name not in local_bound
                ):
                    captured.add(base_name)
            for nested_function in self._nested_function_defs(function):
                collect_from_nested(nested_function, shadowed | local_bound)

        for nested_function in self._nested_function_defs(node):
            collect_from_nested(nested_function, set())
        return captured

    def visit_sequence(self, body: list[ast.stmt]) -> list[ast.stmt]:
        rewritten = []
        for node in body:
            if node is None:
                continue
            updated = self.visit(node)
            if updated is None:
                continue
            if isinstance(updated, list):
                rewritten.extend(updated)
            else:
                rewritten.append(updated)
            if isinstance(updated, ast.FunctionDef):
                self._set_current_name(strip_ssa_suffix(updated.name), updated.name)
            elif isinstance(updated, ast.ClassDef):
                self._set_current_name(strip_ssa_suffix(updated.name), updated.name)
        return rewritten

    def visit_Module(self, node: ast.Module) -> ast.Module:
        module = copy(node)
        self._push_env()
        module.body = self.visit_sequence(list(node.body))
        self._pop_env()
        module.type_ignores = list(getattr(node, "type_ignores", []))
        return module

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        class_def = copy(node)
        class_def.bases = [self.visit(base) for base in node.bases]
        class_def.keywords = [self.visit(keyword) for keyword in node.keywords]
        class_def.decorator_list = [self.visit(dec) for dec in node.decorator_list]
        class_def.body = []
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                class_def.body.append(self.visit(stmt))
                continue
            if isinstance(stmt, ast.AnnAssign):
                ann_assign = copy(stmt)
                ann_assign.annotation = self.visit(stmt.annotation)
                ann_assign.value = (
                    self.visit(stmt.value) if stmt.value is not None else None
                )
                class_def.body.append(ann_assign)
                continue
            if isinstance(stmt, ast.Assign):
                assign = copy(stmt)
                assign.value = self.visit(stmt.value)
                class_def.body.append(assign)
                continue
            class_def.body.append(copy(stmt))
        return class_def

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        function = copy(node)
        function.args = copy(node.args)
        function.args.args = []
        function.decorator_list = [self.visit(dec) for dec in node.decorator_list]

        initial_env = dict(self._current_env())
        for arg in node.args.args:
            arg_cp = copy(arg)
            arg_cp.annotation = self.visit(arg.annotation) if arg.annotation else None
            initial_env[strip_ssa_suffix(arg.arg)] = arg.arg
            function.args.args.append(arg_cp)

        function.returns = self.visit(node.returns) if node.returns else None
        self._push_env(initial_env)
        self._push_protected(self._captured_bases_in_function(node))
        function.body = self.visit_sequence(list(node.body))
        self._pop_protected()
        self._pop_env()
        return function

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if isinstance(node.ctx, ast.Store):
            return copy(node)
        rewritten = copy(node)
        rewritten.id = self._lookup_name(node.id)
        return rewritten

    def _rewrite_assignment_target(self, target: ast.Name) -> ast.Name:
        target_cp = copy(target)
        base_name = strip_ssa_suffix(target.id)
        current_name = self._current_env().get(base_name, base_name)
        if self._in_module_scope():
            target_cp.id = current_name
            self._set_current_name(base_name, current_name)
            return target_cp
        if base_name in self._current_protected():
            target_cp.id = current_name
            self._set_current_name(base_name, current_name)
            return target_cp
        if base_name in self._current_pinned():
            target_cp.id = current_name
            self._set_current_name(base_name, current_name)
            return target_cp
        fresh_name = self._fresh_name(base_name)
        target_cp.id = fresh_name
        self._set_current_name(base_name, fresh_name)
        return target_cp

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        assign = copy(node)
        assign.value = self.visit(node.value)
        assign.targets = [self._rewrite_assignment_target(t) for t in node.targets]
        return assign

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
        assign = copy(node)
        assign.annotation = self.visit(node.annotation)
        assign.value = self.visit(node.value) if node.value is not None else None
        assert isinstance(node.target, ast.Name), "Expected named annotated assignment"
        assign.target = self._rewrite_assignment_target(node.target)
        return assign

    def visit_If(self, node: ast.If) -> ast.If:
        typed_if = copy(node)
        typed_if.test = self.visit(node.test)
        initial_env = dict(self._current_env())

        self._push_env(initial_env)
        body = self.visit_sequence(list(node.body))
        body_env = self._pop_env()

        self._push_env(initial_env)
        orelse = self.visit_sequence(list(node.orelse))
        else_env = self._pop_env()

        if self._in_module_scope():
            typed_if.body = body
            typed_if.orelse = orelse
            return typed_if

        joined_env = self._branch_join_names(initial_env, body_env, else_env)
        typed_if.body = self._append_branch_joins(body, body_env, joined_env)
        typed_if.orelse = self._append_branch_joins(orelse, else_env, joined_env)
        self._current_env().update(joined_env)
        return typed_if

    def _rewrite_loop(self, node: ast.While | ast.For) -> list[ast.stmt]:
        if self._in_module_scope():
            rewritten_loop = copy(node)
            if isinstance(node, ast.While):
                rewritten_loop.test = self.visit(node.test)
            else:
                rewritten_loop.iter = self.visit(node.iter)
                rewritten_loop.target = copy(node.target)
            rewritten_loop.body = self.visit_sequence(list(node.body))
            rewritten_loop.orelse = self.visit_sequence(list(node.orelse))
            return [rewritten_loop]

        pinned_bases = self._written_bases(node) - self._current_protected()
        prelude = []
        for base_name in sorted(pinned_bases):
            had_current_name = base_name in self._current_env()
            current_name = self._current_env().get(base_name, base_name)
            fresh_name = self._fresh_name(base_name)
            if had_current_name:
                prelude.append(
                    self._make_assign(
                        fresh_name, current_name, self._orig_name_value(base_name)
                    )
                )
            self._set_current_name(base_name, fresh_name)

        self._pin_bases(pinned_bases)
        rewritten_loop = copy(node)
        if isinstance(node, ast.While):
            rewritten_loop.test = self.visit(node.test)
        else:
            rewritten_loop.iter = self.visit(node.iter)
            assert isinstance(node.target, ast.Name), "Expected simple for-loop target"
            target_cp = copy(node.target)
            base_name = strip_ssa_suffix(node.target.id)
            target_cp.id = self._lookup_name(base_name)
            rewritten_loop.target = target_cp
        rewritten_loop.body = self.visit_sequence(list(node.body))
        rewritten_loop.orelse = self.visit_sequence(list(node.orelse))
        self._unpin_bases()
        return prelude + [rewritten_loop]

    def visit_While(self, node: ast.While) -> list[ast.stmt]:
        return self._rewrite_loop(node)

    def visit_For(self, node: ast.For) -> list[ast.stmt]:
        return self._rewrite_loop(node)
