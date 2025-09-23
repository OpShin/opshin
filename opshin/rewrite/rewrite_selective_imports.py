import ast
from ast import *
from ..util import CompilingNodeTransformer
from ..type_inference import INITIAL_SCOPE

"""
Handles selective imports by making non-imported names invisible to type inference
while keeping them available for dependencies
"""


class RewriteSelectiveImports(CompilingNodeTransformer):
    step = "Processing selective imports"

    def __init__(self):
        self.selective_imports = {}

    def visit_Module(self, node: Module) -> Module:
        # Extract selective imports information from the module (set by RewriteImport)
        if hasattr(node, "selective_imports"):
            self.selective_imports = node.selective_imports

        # Store selective import info in the module for type inference to use
        node.selective_imports = self.selective_imports
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        # Mark functions as hidden if they weren't explicitly imported
        if self._should_hide_name(node.name):
            node.hidden_from_type_inference = True
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        # Mark classes as hidden if they weren't explicitly imported
        if self._should_hide_name(node.name):
            node.hidden_from_type_inference = True
        return self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> Assign:
        # Mark variable assignments as hidden if they weren't explicitly imported
        for target in node.targets:
            if isinstance(target, Name) and self._should_hide_name(target.id):
                node.hidden_from_type_inference = True
                break
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: AnnAssign) -> AnnAssign:
        # Mark annotated assignments as hidden if they weren't explicitly imported
        if isinstance(node.target, Name) and self._should_hide_name(node.target.id):
            node.hidden_from_type_inference = True
        return self.generic_visit(node)

    def _should_hide_name(self, name: str) -> bool:
        """Check if a name should be hidden from type inference"""
        # If no selective imports were made, don't hide anything (star import behavior)
        if not self.selective_imports:
            return False

        # Check if this name was explicitly imported from any module
        for module_name, imported_names in self.selective_imports.items():
            if name in imported_names:
                return False

        # Name wasn't explicitly imported, so hide it
        return True
