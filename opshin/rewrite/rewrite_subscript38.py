from ast import *
import typing

from ..util import CompilingNodeTransformer

"""
Rewrites all Index/Slice occurrences such that they look like in Python 3.9 onwards (not like Python 3.8).
"""


class RewriteSubscript38(CompilingNodeTransformer):
    step = "Rewriting Subscripts"

    def visit_Index(self, node: Index) -> AST:
        return self.visit(node.value)
