from ast import *

from ..util import CompilingNodeTransformer

"""
Keeps comparison chains intact.

Historically this pass rewrote `a < b < c` into `a < b and b < c`,
which re-evaluated middle expressions and broke Python semantics.
Comparison chains are now compiled directly so each middle expression
is evaluated at most once.
"""


class RewriteComparisonChaining(CompilingNodeTransformer):
    step = "Rewriting comparison chaining"

    def visit_Compare(self, node: Compare) -> Compare:
        return self.generic_visit(node)
