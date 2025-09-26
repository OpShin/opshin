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
        # Remove function definitions that weren't explicitly imported
        # but keep them if they might be dependencies
        if self._should_hide_name(node.name):
            # Instead of hiding, we'll remove the function from the top level
            # and let dead code analysis handle unused dependencies
            return None  # This will remove the node
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        # Remove class definitions that weren't explicitly imported
        if self._should_hide_name(node.name):
            return None  # This will remove the node
        return self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> Assign:
        # Remove variable assignments that weren't explicitly imported
        for target in node.targets:
            if isinstance(target, Name) and self._should_hide_name(target.id):
                return None  # This will remove the node
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: AnnAssign) -> AnnAssign:
        # Remove annotated assignments that weren't explicitly imported
        if isinstance(node.target, Name) and self._should_hide_name(node.target.id):
            return None  # This will remove the node
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
