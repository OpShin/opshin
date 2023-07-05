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
        if node.ctx == Store() and node.id in FORBIDDEN_NAMES:
            raise ForbiddenOverwriteError(
                f"It is not allowed to overwrite name {node.id}"
            )
        return node
