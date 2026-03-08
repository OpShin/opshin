from ast import *
from copy import copy

from ..type_impls import FunctionType, InstanceType
from ..util import CompilingNodeTransformer, CompilingNodeVisitor


class _DirectFunctionCallCollector(CompilingNodeVisitor):
    def __init__(self, function_names: set[str]):
        self.function_names = function_names
        self.called = set()

    def visit_Call(self, node: Call):
        if isinstance(node.func, Name) and node.func.id in self.function_names:
            self.called.add(node.func.id)
        self.generic_visit(node)


class OptimizeRewriteFunctionClosures(CompilingNodeTransformer):
    step = "Rewriting function closures"

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

    def _update_function_bound_vars(self, body: list[stmt]):
        function_nodes = self._collect_typed_functions(body)
        if not function_nodes:
            return

        function_names = {f.name for f in function_nodes}
        function_indices = {f.name: i for i, f in enumerate(function_nodes)}
        function_types = {f.name: f.typ for f in function_nodes}

        direct_called_funcs = {}
        required_direct_funcs = {}
        direct_non_function_bound_vars = {}
        self_recursive = {}
        for function in function_nodes:
            old_bound_vars = dict(function.typ.typ.bound_vars)
            direct_non_function_bound_vars[function.name] = {
                name: typ
                for name, typ in old_bound_vars.items()
                if name not in function_names
            }

            collector = _DirectFunctionCallCollector(function_names)
            for s in function.body:
                collector.visit(s)
            direct_called_funcs[function.name] = collector.called
            self_recursive[function.name] = function.name in collector.called

            required_funcs = set()
            if self_recursive[function.name]:
                required_funcs.add(function.name)
            for called_name in collector.called:
                if function_indices[called_name] > function_indices[function.name]:
                    required_funcs.add(called_name)
            required_direct_funcs[function.name] = required_funcs

        required_func_closure = copy(required_direct_funcs)
        changed = True
        while changed:
            changed = False
            new_required_func_closure = {}
            for function in function_nodes:
                fn_name = function.name
                resolved = set(required_direct_funcs[fn_name])
                for called_name in direct_called_funcs[fn_name]:
                    for dep_name in required_func_closure[called_name]:
                        if function_indices[dep_name] < function_indices[fn_name]:
                            continue
                        resolved.add(dep_name)
                new_required_func_closure[fn_name] = resolved
            changed = any(
                new_required_func_closure[function.name]
                != required_func_closure[function.name]
                for function in function_nodes
            )
            required_func_closure = new_required_func_closure

        for function in function_nodes:
            old_function_type = function.typ.typ
            new_bound_vars = dict(direct_non_function_bound_vars[function.name])
            for dep_name in sorted(required_func_closure[function.name]):
                dep_type = function_types.get(dep_name)
                if dep_type is None:
                    continue
                new_bound_vars[dep_name] = dep_type
            function.typ = InstanceType(
                FunctionType(
                    argtyps=list(old_function_type.argtyps),
                    rettyp=old_function_type.rettyp,
                    bound_vars=new_bound_vars,
                    bind_self=function.name if self_recursive[function.name] else None,
                )
            )

        refreshed_function_types = {f.name: f.typ for f in function_nodes}
        for node in walk(Module(body=body, type_ignores=[])):
            if (
                isinstance(node, Name)
                and isinstance(node.ctx, Load)
                and node.id in refreshed_function_types
            ):
                node.typ = refreshed_function_types[node.id]

    def visit_Module(self, node: Module) -> Module:
        module = copy(node)
        module.body = list(node.body)
        module.type_ignores = list(getattr(node, "type_ignores", []))
        self._update_function_bound_vars(module.body)
        return module
