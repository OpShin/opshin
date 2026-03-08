from ast import *
from copy import copy

from ..type_impls import FunctionType, InstanceType
from ..rewrite.rewrite_cast_condition import SPECIAL_BOOL
from ..type_inference import INITIAL_SCOPE, union_types
from ..util import (
    CompilingNodeTransformer,
    CompilingNodeVisitor,
    externally_bound_vars,
)


class _DirectFunctionCallCollector(CompilingNodeVisitor):
    def __init__(self, function_ids: set[str]):
        self.function_ids = function_ids
        self.called: dict[str, str] = {}

    def visit_Call(self, node: Call):
        if (
            isinstance(node.func, Name)
            and hasattr(node.func, "typ")
            and isinstance(node.func.typ, InstanceType)
            and isinstance(node.func.typ.typ, FunctionType)
            and node.func.typ.typ.function_id is not None
            and node.func.typ.typ.function_id in self.function_ids
        ):
            self.called[node.func.id] = node.func.typ.typ.function_id
        self.generic_visit(node)

    def visit_Compare(self, node: Compare):
        # Compare nodes can lower to lifted dunder functions during
        # compilation, so those call-like dependencies need to participate in
        # the same closure analysis as explicit Call nodes.
        for dunder_override in getattr(node, "dunder_overrides", []):
            if dunder_override is None:
                continue
            function_type = getattr(dunder_override, "function_type", None)
            if not (
                isinstance(function_type, InstanceType)
                and isinstance(function_type.typ, FunctionType)
                and function_type.typ.function_id in self.function_ids
            ):
                continue
            self.called[dunder_override.method_name] = function_type.typ.function_id
        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef):
        return None


class OptimizeRewriteFunctionClosures(CompilingNodeTransformer):
    # Function values are compiled as explicit closures. This pass computes
    # which names each function must receive so recursive calls, aliases and
    # lifted methods all see the same environment the type checker inferred.
    step = "Resolving function dependencies"

    def _merge_envs(
        self, s1: dict[str, InstanceType], s2: dict[str, InstanceType]
    ) -> dict[str, InstanceType]:
        merged = dict(s1)
        for key, value in s2.items():
            if key not in merged:
                merged[key] = value
                continue
            if merged[key] == value:
                continue
            if isinstance(merged[key], InstanceType) and isinstance(
                value, InstanceType
            ):
                if isinstance(merged[key].typ, FunctionType) and isinstance(
                    value.typ, FunctionType
                ):
                    if merged[key].typ >= value.typ:
                        continue
                    if value.typ >= merged[key].typ:
                        merged[key] = value
                        continue
                merged[key] = InstanceType(union_types(merged[key].typ, value.typ))
                continue
            merged[key] = value
        return merged

    def _collect_typed_functions(self, body: list[stmt]) -> list[FunctionDef]:
        functions = []
        for s in body:
            if not isinstance(s, FunctionDef):
                continue
            if not (
                hasattr(s, "typ")
                and isinstance(s.typ, InstanceType)
                and isinstance(s.typ.typ, FunctionType)
            ):
                continue
            functions.append(s)
        return functions

    def _collect_external_name_types(
        self, function: FunctionDef, external_names: set[str]
    ) -> dict[str, InstanceType]:
        class ExternalNameTypeCollector(CompilingNodeVisitor):
            def __init__(self, target_names: set[str]):
                self.target_names = target_names
                self.types = {}

            def visit_AnnAssign(self, node) -> None:
                self.visit(node.value)
                self.visit(node.target)

            def visit_FunctionDef(self, node) -> None:
                for stmt in node.body:
                    self.visit(stmt)

            def visit_Name(self, node: Name) -> None:
                if (
                    isinstance(node.ctx, Load)
                    and node.id in self.target_names
                    and hasattr(node, "typ")
                ):
                    self.types.setdefault(node.id, node.typ)

            def visit_Compare(self, node: Compare) -> None:
                for dunder_override in getattr(node, "dunder_overrides", []):
                    if (
                        dunder_override is not None
                        and dunder_override.method_name in self.target_names
                        and isinstance(dunder_override.function_type, InstanceType)
                        and isinstance(dunder_override.function_type.typ, FunctionType)
                    ):
                        self.types.setdefault(
                            dunder_override.method_name, dunder_override.function_type
                        )
                self.generic_visit(node)

            def visit_ClassDef(self, node: ClassDef):
                pass

        collector = ExternalNameTypeCollector(external_names)
        collector.visit(function)
        return collector.types

    def _refresh_node_types_from_env(self, node: AST, env: dict[str, InstanceType]):
        class SequenceBindingRefresher(NodeTransformer):
            def __init__(self, current_env: dict[str, InstanceType]):
                self.current_env = current_env

            def visit_FunctionDef(self, node: FunctionDef):
                return node

            def visit_ClassDef(self, node: ClassDef):
                return node

            def visit_Name(self, node: Name):
                if (
                    isinstance(node.ctx, Load)
                    and node.id in self.current_env
                    and isinstance(self.current_env[node.id], InstanceType)
                    and isinstance(self.current_env[node.id].typ, FunctionType)
                    and hasattr(node, "typ")
                ):
                    node.typ = self.current_env[node.id]
                return node

            def visit_Compare(self, node: Compare):
                for dunder_override in getattr(node, "dunder_overrides", []):
                    if dunder_override is None:
                        continue
                    method_name = dunder_override.method_name
                    if (
                        method_name in self.current_env
                        and isinstance(self.current_env[method_name], InstanceType)
                        and isinstance(self.current_env[method_name].typ, FunctionType)
                    ):
                        dunder_override.function_type = self.current_env[method_name]
                return self.generic_visit(node)

        SequenceBindingRefresher(env).visit(node)

    def _refresh_sequence_binding_uses(self, body: list[stmt]):
        self._refresh_sequence_binding_uses_with_env(body, {})

    def _refresh_sequence_binding_uses_with_env(
        self, body: list[stmt], inherited_env: dict[str, InstanceType]
    ) -> dict[str, InstanceType]:
        # Re-thread the current function-valued environment through the local
        # statement sequence so aliases like `f = odd` pick up the final
        # closure type before later dependency collection runs.
        current_env = dict(inherited_env)
        for stmt in body:
            if isinstance(stmt, FunctionDef):
                current_env[stmt.name] = stmt.typ

        for stmt in body:
            if isinstance(stmt, FunctionDef):
                continue
            current_env = self._refresh_statement_binding_uses(stmt, current_env)

        for stmt in body:
            if not isinstance(stmt, FunctionDef):
                continue
            function_env = dict(current_env)
            for arg in stmt.args.args:
                if hasattr(arg, "typ"):
                    function_env[arg.arg] = arg.typ
            self._refresh_sequence_binding_uses_with_env(stmt.body, function_env)

        return current_env

    def _refresh_statement_binding_uses(
        self, stmt: stmt, current_env: dict[str, InstanceType]
    ) -> dict[str, InstanceType]:
        self._refresh_node_types_from_env(stmt, current_env)

        if isinstance(stmt, Assign):
            for target in stmt.targets:
                if (
                    isinstance(target, Name)
                    and hasattr(stmt.value, "typ")
                    and isinstance(stmt.value.typ, InstanceType)
                    and isinstance(stmt.value.typ.typ, FunctionType)
                ):
                    target.typ = stmt.value.typ
                    current_env[target.id] = stmt.value.typ
            return current_env

        if isinstance(stmt, AnnAssign):
            if (
                isinstance(stmt.target, Name)
                and hasattr(stmt.value, "typ")
                and isinstance(stmt.value.typ, InstanceType)
                and isinstance(stmt.value.typ.typ, FunctionType)
            ):
                stmt.target.typ = stmt.value.typ
                current_env[stmt.target.id] = stmt.value.typ
            return current_env

        if isinstance(stmt, If):
            body_env = self._refresh_sequence_binding_uses_with_env(
                stmt.body, dict(current_env)
            )
            else_env = self._refresh_sequence_binding_uses_with_env(
                stmt.orelse, dict(current_env)
            )
            return self._merge_envs(body_env, else_env)

        if isinstance(stmt, (While, For)):
            body_env = self._refresh_sequence_binding_uses_with_env(
                stmt.body, dict(current_env)
            )
            else_env = self._refresh_sequence_binding_uses_with_env(
                stmt.orelse, dict(current_env)
            )
            return self._merge_envs(body_env, else_env)

        return current_env

    def _update_function_bound_vars(self, body: list[stmt]):
        function_nodes = self._collect_typed_functions(body)
        if not function_nodes:
            return

        function_node_by_id = {}
        function_type_by_name = {}
        for function in function_nodes:
            function_id = function.typ.typ.function_id
            assert function_id is not None, "Function type is missing function_id"
            function_node_by_id[function_id] = function
            function_type_by_name[function.name] = function.typ

        function_types = {
            function_id: node.typ for function_id, node in function_node_by_id.items()
        }
        function_ids = set(function_types.keys())

        direct_external_bound_vars = {}
        direct_required_names = {}
        called_function_targets = {}
        for function in function_nodes:
            function_id = function.typ.typ.function_id
            assert function_id is not None, "Function type is missing function_id"
            direct_external_names = {
                name
                for name in externally_bound_vars(function)
                if name not in ["List", "Dict"]
                and name not in INITIAL_SCOPE
                and not name.startswith(SPECIAL_BOOL)
            }
            direct_external_bound_vars[function_id] = self._collect_external_name_types(
                function, direct_external_names
            )
            direct_required_names[function_id] = set(
                direct_external_bound_vars[function_id]
            )
            if function.typ.typ.bind_self is not None:
                direct_required_names[function_id].add(function.name)

            collector = _DirectFunctionCallCollector(function_ids)
            for stmt in function.body:
                collector.visit(stmt)
            called_function_targets[function_id] = set(collector.called.values())
            direct_required_names[function_id].update(collector.called.keys())

        # Solve closure requirements as a fixed point over the local call graph:
        # if `f` calls `g`, then `f` must be able to supply everything `g`
        # needs when `g` is invoked at runtime.
        required_names = copy(direct_required_names)
        changed = True
        while changed:
            changed = False
            new_required_names = {}
            for function_id in function_types:
                resolved = set(direct_required_names[function_id])
                for dep_id in called_function_targets[function_id]:
                    resolved.update(required_names[dep_id])
                new_required_names[function_id] = resolved
            changed = any(
                new_required_names[function_id] != required_names[function_id]
                for function_id in function_types
            )
            required_names = new_required_names

        available_name_types: dict[str, InstanceType] = dict(function_type_by_name)
        for bound_vars in direct_external_bound_vars.values():
            for name, typ in bound_vars.items():
                if name in function_type_by_name:
                    available_name_types[name] = function_type_by_name[name]
                    continue
                if name not in available_name_types:
                    available_name_types[name] = typ
                    continue
                available_name_types = self._merge_envs(
                    available_name_types, {name: typ}
                )

        for function in function_nodes:
            function_id = function.typ.typ.function_id
            assert function_id is not None, "Function type is missing function_id"
            old_function_type = function.typ.typ
            function_required_names = required_names[function_id]
            bind_self = (
                function.name if function.name in function_required_names else None
            )
            new_bound_vars = {
                name: available_name_types[name]
                for name in function_required_names
                if name != function.name and name in available_name_types
            }
            function.typ = InstanceType(
                FunctionType(
                    argtyps=list(old_function_type.argtyps),
                    rettyp=old_function_type.rettyp,
                    bound_vars=new_bound_vars,
                    bind_self=bind_self,
                    function_id=old_function_type.function_id,
                )
            )

        refreshed_function_types = {
            function.name: function.typ for function in function_nodes
        }
        for node in walk(Module(body=body, type_ignores=[])):
            if (
                isinstance(node, Name)
                and isinstance(node.ctx, Load)
                and node.id in refreshed_function_types
            ):
                node.typ = refreshed_function_types[node.id]

        self._refresh_sequence_binding_uses(body)

    def _rewrite_sequence(self, body: list[stmt]) -> list[stmt]:
        rewritten_body = [self.visit(stmt) for stmt in body]
        self._update_function_bound_vars(rewritten_body)
        return rewritten_body

    def visit_Module(self, node: Module) -> Module:
        module = copy(node)
        module.body = self._rewrite_sequence(list(node.body))
        module.type_ignores = list(getattr(node, "type_ignores", []))
        return module

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        function = copy(node)
        function.body = self._rewrite_sequence(list(node.body))
        return function

    def visit_If(self, node: If) -> If:
        typed_if = copy(node)
        typed_if.body = self._rewrite_sequence(list(node.body))
        typed_if.orelse = self._rewrite_sequence(list(node.orelse))
        return typed_if

    def visit_While(self, node: While) -> While:
        typed_while = copy(node)
        typed_while.body = self._rewrite_sequence(list(node.body))
        typed_while.orelse = self._rewrite_sequence(list(node.orelse))
        return typed_while

    def visit_For(self, node: For) -> For:
        typed_for = copy(node)
        typed_for.body = self._rewrite_sequence(list(node.body))
        typed_for.orelse = self._rewrite_sequence(list(node.orelse))
        return typed_for
