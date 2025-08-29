from ast import *

from ..util import CompilingNodeTransformer

"""
Make sure that certain variable names may never be overwritten
"""

FORBIDDEN_NAMES = {
    # type check
    "isinstance",
    # Type annotations
    "List",
    "Dict",
    "Union",
    "Self",
    # decorator and class name
    "dataclass",
    "PlutusData",
    # special decorator marking wrapped builtins
    "wraps_builtin",
}


class ForbiddenOverwriteError(ValueError):
    pass


class RewriteForbiddenOverwrites(CompilingNodeTransformer):
    step = "Checking for forbidden name overwrites"

    def visit_Name(self, node: Name) -> Name:
        if isinstance(node.ctx, Store) and node.id in FORBIDDEN_NAMES:
            raise ForbiddenOverwriteError(
                f"It is not allowed to overwrite name {node.id}"
            )
        return node

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        # Check if the function name is forbidden
        if node.name in FORBIDDEN_NAMES:
            raise ForbiddenOverwriteError(
                f"It is not allowed to overwrite name {node.name}"
            )
        for arg in node.args.args:
            if arg.arg in FORBIDDEN_NAMES:
                raise ForbiddenOverwriteError(
                    f"It is not allowed to overwrite name {arg.arg}"
                )
        node.body = [self.visit(n) for n in node.body]
        return node

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        # Check if the class name is forbidden
        if node.name in FORBIDDEN_NAMES:
            raise ForbiddenOverwriteError(
                f"It is not allowed to overwrite name {node.name}"
            )
        node.body = [self.visit(n) for n in node.body]
        return node
