import ast
from ast import Assign, ClassDef, FunctionDef, Load, Module, Name, Store
from copy import copy, deepcopy

from ..typed_util import FlatteningScopedSequenceNodeTransformer
from ..util import NameSupply, custom_fix_missing_locations


class RewriteClassConstrId(ast.NodeTransformer):
    """Resolve direct expression loads from the one supported class binding."""

    def __init__(self, constr_id: int):
        self.constr_id = constr_id

    def visit_Name(self, node: Name):
        if isinstance(node.ctx, Load) and node.id == "CONSTR_ID":
            return ast.copy_location(ast.Constant(value=self.constr_id), node)
        return node

    def visit_Lambda(self, node: ast.Lambda):
        # Class scopes do not enclose nested function scopes.
        return node

    def _visit_comprehension(self, node):
        # Only the outermost iterable is evaluated in the surrounding class
        # scope; the rest runs in the comprehension's implicit function scope.
        node.generators[0].iter = self.visit(node.generators[0].iter)
        return node

    visit_ListComp = _visit_comprehension
    visit_SetComp = _visit_comprehension
    visit_DictComp = _visit_comprehension
    visit_GeneratorExp = _visit_comprehension


class RewriteDefaultArguments(FlatteningScopedSequenceNodeTransformer):
    """Evaluate function defaults once and replace them with hidden bindings."""

    step = "Hoisting default arguments"

    def visit_Module(self, node: Module) -> Module:
        self.name_supply = NameSupply.from_tree(node, "default")
        return super().visit_Module(node)

    def _hoist_function_defaults(self, function: FunctionDef):
        function.args = copy(function.args)
        bindings = []
        rewritten_defaults = []
        for default in function.args.defaults:
            name = self.name_supply.fresh_name()
            target = custom_fix_missing_locations(Name(id=name, ctx=Store()), default)
            value = self.visit(default)
            binding = custom_fix_missing_locations(
                Assign(targets=[target], value=value), default
            )
            binding.is_default_argument_binding = True
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
        constr_id = None
        for statement in node.body:
            if isinstance(statement, FunctionDef):
                method_source = statement
                if constr_id is not None:
                    method_source = copy(statement)
                    method_source.args = copy(statement.args)
                    rewriter = RewriteClassConstrId(constr_id)
                    method_source.args.defaults = [
                        rewriter.visit(deepcopy(default))
                        for default in statement.args.defaults
                    ]
                *method_bindings, method = self.visit_FunctionDef(method_source)
                bindings.extend(method_bindings)
                class_def.body.append(method)
            else:
                class_def.body.append(self.visit(statement))
                target = None
                if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                    target = statement.targets[0]
                elif isinstance(statement, ast.AnnAssign):
                    target = statement.target
                if (
                    isinstance(target, Name)
                    and target.id == "CONSTR_ID"
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, int)
                ):
                    constr_id = statement.value.value
        return [*bindings, class_def]
