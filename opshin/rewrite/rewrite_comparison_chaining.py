from ast import *
from copy import copy

from ..util import CompilingNodeTransformer

"""
Rewrites all occurences of comparison chaining into normal comparisons.
"""


class RewriteComparisonChaining(CompilingNodeTransformer):
    step = "Rewriting comparison chaining"

    def visit_Compare(self, node: Compare) -> Compare:
        if len(node.ops) <= 1:
            return self.generic_visit(node)
        new_node = BoolOp(
            op=And(),
            values=[
                Compare(
                    left=node.left,
                    ops=node.ops[:1],
                    comparators=node.comparators[:1],
                ),
                self.visit(
                    Compare(
                        left=node.comparators[0],
                        ops=node.ops[1:],
                        comparators=node.comparators[1:],
                    )
                ),
            ],
        )
        return self.generic_visit(new_node)
