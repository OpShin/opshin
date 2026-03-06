from ast import *

from ..util import CompilingNodeTransformer

"""
Retains chained comparisons for later compilation.

Chained comparisons need to preserve Python semantics:
- evaluate each operand at most once
- stop evaluating operands as soon as a comparison fails

These guarantees are implemented directly in the compiler where operand
evaluation can be cached in generated UPLC terms.
"""


class RewriteComparisonChaining(CompilingNodeTransformer):
    step = "Rewriting comparison chaining"

    def visit_Compare(self, node: Compare) -> Compare:
        return self.generic_visit(node)
