from _ast import FunctionDef
from ast import *
from typing import Any
from ..util import CompilingNodeTransformer

"""
Expand union types
"""


class OptimizeUnionExpansion(CompilingNodeTransformer):
    step = "Expanding Unions"

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        return super().visit_FunctionDef(node)
