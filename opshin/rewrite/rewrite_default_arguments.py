from ast import Assign, ClassDef, FunctionDef, Load, Module, Name, Store
from copy import copy

from ..typed_util import FlatteningScopedSequenceNodeTransformer
from ..util import NameSupply, custom_fix_missing_locations


class RewriteDefaultArguments(FlatteningScopedSequenceNodeTransformer):
    """Evaluate function defaults once and replace them with hidden bindings."""

    step = "Hoisting default arguments"

    def visit_Module(self, node: Module) -> Module:
        self.name_supply = NameSupply.from_tree(node)
        return super().visit_Module(node)

    def _hoist_function_defaults(self, function: FunctionDef):
        function.args = copy(function.args)
        bindings = []
        rewritten_defaults = []
        for default in function.args.defaults:
            name = self.name_supply.fresh_name("__opshin_default_")
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
