from ast import *
from copy import copy

from ..type_impls import CLOSURE_PLACEHOLDER, FunctionType, InstanceType
from ..rewrite.rewrite_cast_condition import SPECIAL_BOOL
from ..type_inference import INITIAL_SCOPE, union_types
from ..typed_util import (
    ScopedSequenceNodeTransformer,
    collect_typed_functions,
)
from ..util import (
    CompilingNodeVisitor,
    externally_bound_vars,
    read_vars,
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


class _FunctionTypeRewriter(NodeTransformer):
    def __init__(self, function_types_by_id: dict[str, FunctionType]):
        self.function_types_by_id = function_types_by_id

    def _rewrite_function_instance_type(
        self, typ: InstanceType | None
    ) -> InstanceType | None:
        if not (
            isinstance(typ, InstanceType)
            and isinstance(typ.typ, FunctionType)
            and typ.typ.function_id is not None
        ):
            return typ
        resolved = self.function_types_by_id.get(typ.typ.function_id)
        if resolved is None:
            return typ
        return InstanceType(resolved)

    def generic_visit(self, node: AST):
        node = super().generic_visit(node)
        if hasattr(node, "typ"):
            node.typ = self._rewrite_function_instance_type(node.typ)
        return node

    def visit_Compare(self, node: Compare):
        node = self.generic_visit(node)
        for dunder_override in getattr(node, "dunder_overrides", []):
            if dunder_override is None:
                continue
            dunder_override.function_type = self._rewrite_function_instance_type(
                dunder_override.function_type
            )
        return node


class OptimizeRewriteFunctionClosures(ScopedSequenceNodeTransformer):
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

    def _update_function_bound_vars(self, body: list[stmt]):
        function_nodes = collect_typed_functions(body)
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
        direct_bind_self = {}
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
            direct_bind_self[function_id] = function.name in read_vars(function)
            direct_required_names[function_id] = set(
                direct_external_bound_vars[function_id]
            )
            if direct_bind_self[function_id]:
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

    def _reassign_function_types(self, body: list[stmt]):
        module = Module(body=body, type_ignores=[])
        function_types_by_id = {}
        for node in walk(module):
            if not (
                isinstance(node, FunctionDef)
                and hasattr(node, "typ")
                and isinstance(node.typ, InstanceType)
                and isinstance(node.typ.typ, FunctionType)
                and node.typ.typ.function_id is not None
            ):
                continue
            function_types_by_id[node.typ.typ.function_id] = node.typ.typ
        _FunctionTypeRewriter(function_types_by_id).visit(module)

    def _assert_no_closure_placeholders(self, node: AST):
        for child in walk(node):
            if not (
                hasattr(child, "typ")
                and isinstance(child.typ, InstanceType)
                and isinstance(child.typ.typ, FunctionType)
            ):
                continue
            assert (
                child.typ.typ.bound_vars is not CLOSURE_PLACEHOLDER
                and child.typ.typ.bind_self is not CLOSURE_PLACEHOLDER
            ), "Closure rewrite left unresolved function closure metadata"

    def _merge_function_definition_envs(
        self, s1: dict[str, InstanceType], s2: dict[str, InstanceType]
    ) -> dict[str, InstanceType]:
        merged = dict(s1)
        for key, value in s2.items():
            if key not in merged:
                merged[key] = value
                continue
            if merged[key] == value or merged[key] >= value:
                continue
            if value >= merged[key]:
                merged[key] = value
                continue
            raise AssertionError(
                f"Type '{merged[key].python_type()}' of variable '{key}' in local scope does not match inferred type '{value.python_type()}'"
            )
        return merged

    def _validate_function_redefinitions_in_sequence(
        self, body: list[stmt], inherited: dict[str, InstanceType]
    ) -> dict[str, InstanceType]:
        current_env = dict(inherited)
        for node in body:
            if (
                isinstance(node, FunctionDef)
                and hasattr(node, "typ")
                and isinstance(node.typ, InstanceType)
                and isinstance(node.typ.typ, FunctionType)
            ):
                current_env = self._merge_function_definition_envs(
                    current_env, {node.name: node.typ}
                )
                continue
            if isinstance(node, (If, While, For)):
                body_env = self._validate_function_redefinitions_in_sequence(
                    node.body, current_env
                )
                else_env = self._validate_function_redefinitions_in_sequence(
                    node.orelse, current_env
                )
                current_env = self._merge_function_definition_envs(body_env, else_env)
        return current_env

    def _validate_function_redefinitions(self, body: list[stmt]):
        self._validate_function_redefinitions_in_sequence(body, {})

    def visit_sequence(self, body: list[stmt]) -> list[stmt]:
        rewritten_body = super().visit_sequence(body)
        self._update_function_bound_vars(rewritten_body)
        self._reassign_function_types(rewritten_body)
        self._validate_function_redefinitions(rewritten_body)
        return rewritten_body

    def visit_Module(self, node: Module) -> Module:
        module = super().visit_Module(node)
        self._assert_no_closure_placeholders(module)
        return module
