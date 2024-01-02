from ast import *

from ..util import CompilingNodeTransformer

"""
Make sure that returns are not allowed in the outermost scope
"""


class RewriteForbiddenReturn(CompilingNodeTransformer):
    step = "Checking for forbidden return statements"

    def visit_Return(self, node):
        raise SyntaxError(f"Forbidden return statement outside function")

    def visit_FunctionDef(self, node: Name) -> Name:
        # skip the content of the function definition
        return node
