from ast import Assign, ClassDef, FunctionDef, Load, Module, Name, Store, arg, walk
from copy import copy

from ..typed_util import FlatteningScopedSequenceNodeTransformer
from ..util import custom_fix_missing_locations


class RewriteDefaultArguments(FlatteningScopedSequenceNodeTransformer):
    """Evaluate function defaults once and replace them with hidden bindings."""

    step = "Hoisting default arguments"

    def visit_Module(self, node: Module) -> Module:
        self._used_names = set()
        for child in walk(node):
            if isinstance(child, Name):
                self._used_names.add(child.id)
            elif isinstance(child, arg):
                self._used_names.add(child.arg)
            elif isinstance(child, (FunctionDef, ClassDef)):
                self._used_names.add(child.name)
        self._default_index = 0
        return super().visit_Module(node)

    def _fresh_default_name(self) -> str:
        while True:
            name = f"__opshin_default_{self._default_index}"
            self._default_index += 1
            if name not in self._used_names:
                self._used_names.add(name)
                return name

    def _hoist_function_defaults(self, function: FunctionDef):
        function.args = copy(function.args)
        bindings = []
        rewritten_defaults = []
        for default in function.args.defaults:
            name = self._fresh_default_name()
            target = custom_fix_missing_locations(Name(id=name, ctx=Store()), default)
            value = self.visit(default)
            binding = custom_fix_missing_locations(
                Assign(targets=[target], value=value), default
            )
            bindings.append(binding)
            rewritten_defaults.append(
                custom_fix_missing_locations(Name(id=name, ctx=Load()), default)
            )
        function.args.defaults = rewritten_defaults
        return bindings, function

    def visit_FunctionDef(self, node: FunctionDef):
        function = super().visit_FunctionDef(node)
        bindings, function = self._hoist_function_defaults(function)
        return [*bindings, function]

    def visit_ClassDef(self, node: ClassDef):
        class_def = copy(node)
        class_def.body = []
        bindings = []
        for statement in node.body:
            if isinstance(statement, FunctionDef):
                *method_bindings, method = self.visit_FunctionDef(statement)
                bindings.extend(method_bindings)
                class_def.body.append(method)
            else:
                class_def.body.append(self.visit(statement))
        return [*bindings, class_def]
