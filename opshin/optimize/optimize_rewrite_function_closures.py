from ast import *
from copy import copy

from ..type_impls import FunctionType, InstanceType
from ..util import (
    CompilingNodeTransformer,
    CompilingNodeVisitor,
    externally_bound_vars,
)


class _DirectFunctionCallCollector(CompilingNodeVisitor):
    def __init__(self, function_names: set[str]):
        self.function_names = function_names
        self.called = set()

    def visit_Call(self, node: Call):
        if isinstance(node.func, Name) and node.func.id in self.function_names:
            self.called.add(node.func.id)
        self.generic_visit(node)


class OptimizeRewriteFunctionClosures(CompilingNodeTransformer):
    step = "Resolving function dependencies"

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
                    and hasattr(node, "typ")
                ):
                    node.typ = self.current_env[node.id]
                return node

        SequenceBindingRefresher(env).visit(node)

    def _refresh_sequence_binding_uses(self, body: list[stmt]):
        current_env = {}
        for stmt in body:
            if isinstance(stmt, FunctionDef):
                current_env[stmt.name] = stmt.typ
                continue

            self._refresh_node_types_from_env(stmt, current_env)

            if isinstance(stmt, Assign):
                for target in stmt.targets:
                    if isinstance(target, Name) and hasattr(stmt.value, "typ"):
                        target.typ = stmt.value.typ
                        current_env[target.id] = stmt.value.typ
            elif isinstance(stmt, AnnAssign):
                if isinstance(stmt.target, Name) and hasattr(stmt.value, "typ"):
                    stmt.target.typ = stmt.value.typ
                    current_env[stmt.target.id] = stmt.value.typ

    def _update_function_bound_vars(self, body: list[stmt]):
        function_nodes = self._collect_typed_functions(body)
        if not function_nodes:
            return

        function_indices = {
            id(function): i for i, function in enumerate(function_nodes)
        }
        last_def_index = {}
        last_def_node_by_name = {}
        for i, function in enumerate(function_nodes):
            last_def_index[function.name] = i
            last_def_node_by_name[function.name] = function

        function_names = set(last_def_index.keys())
        function_types = {
            name: node.typ for name, node in last_def_node_by_name.items()
        }

        required_direct_funcs = {}
        direct_non_function_bound_vars = {}
        called_function_targets = {}
        for function in function_nodes:
            direct = {
                name
                for name in externally_bound_vars(function)
                if name not in ["List", "Dict"]
            }
            direct_non_function_names = direct.difference(function_names)
            direct_non_function_bound_vars[id(function)] = (
                self._collect_external_name_types(function, direct_non_function_names)
            )

            collector = _DirectFunctionCallCollector(function_names)
            collector.visit(function)
            called_function_targets[id(function)] = [
                id(last_def_node_by_name[called_name])
                for called_name in collector.called
                if called_name in last_def_node_by_name
            ]

            required_funcs = set()
            if (
                function.name in collector.called
                and last_def_node_by_name[function.name] is function
            ):
                required_funcs.add(function.name)
            for called_name in collector.called:
                if last_def_index[called_name] > function_indices[id(function)]:
                    required_funcs.add(called_name)
            for sibling_name in getattr(function, "self_called_method_names", set()):
                if sibling_name in function_names and (
                    last_def_index[sibling_name] > function_indices[id(function)]
                ):
                    required_funcs.add(sibling_name)
            required_direct_funcs[id(function)] = required_funcs

        node_by_id = {id(function): function for function in function_nodes}
        graph = {
            id(function): called_function_targets[id(function)]
            for function in function_nodes
        }

        index = 0
        stack = []
        stack_members = set()
        indices = {}
        lowlinks = {}
        recursive_component_names = {}

        def strongconnect(node_id: int):
            nonlocal index
            indices[node_id] = index
            lowlinks[node_id] = index
            index += 1
            stack.append(node_id)
            stack_members.add(node_id)

            for dep_id in graph[node_id]:
                if dep_id not in indices:
                    strongconnect(dep_id)
                    lowlinks[node_id] = min(lowlinks[node_id], lowlinks[dep_id])
                elif dep_id in stack_members:
                    lowlinks[node_id] = min(lowlinks[node_id], indices[dep_id])

            if lowlinks[node_id] != indices[node_id]:
                return

            component = []
            while True:
                member = stack.pop()
                stack_members.remove(member)
                component.append(member)
                if member == node_id:
                    break

            if len(component) > 1 or node_id in graph[node_id]:
                component_names = {node_by_id[member].name for member in component}
            else:
                component_names = set()
            for member in component:
                recursive_component_names[member] = component_names

        for function in function_nodes:
            node_id = id(function)
            if node_id not in indices:
                strongconnect(node_id)

        for function in function_nodes:
            recursive_component_names.setdefault(id(function), set())

        required_func_closure = copy(required_direct_funcs)
        changed = True
        while changed:
            changed = False
            new_required_func_closure = {}
            for function in function_nodes:
                node_id = id(function)
                resolved = set(required_direct_funcs[node_id]).union(
                    recursive_component_names[node_id]
                )
                for dep_id in called_function_targets[node_id]:
                    for dep_name in required_func_closure[dep_id]:
                        resolved.add(dep_name)
                new_required_func_closure[node_id] = resolved
            changed = any(
                new_required_func_closure[id(function)]
                != required_func_closure[id(function)]
                for function in function_nodes
            )
            required_func_closure = new_required_func_closure

        for function in function_nodes:
            old_function_type = function.typ.typ
            new_bound_vars = dict(direct_non_function_bound_vars[id(function)])
            bind_self = (
                function.name
                if (
                    function.name in required_func_closure[id(function)]
                    and last_def_node_by_name[function.name] is function
                )
                else None
            )
            for dep_name in sorted(required_func_closure[id(function)]):
                if bind_self is not None and dep_name == function.name:
                    continue
                dep_type = function_types.get(dep_name)
                if dep_type is None:
                    continue
                new_bound_vars[dep_name] = dep_type
            function.typ = InstanceType(
                FunctionType(
                    argtyps=list(old_function_type.argtyps),
                    rettyp=old_function_type.rettyp,
                    bound_vars=new_bound_vars,
                    bind_self=bind_self,
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
