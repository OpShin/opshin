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
        all_comparators = [node.left] + node.comparators
        compare_values = []
        for comparator_left, comparator_right, op in zip(
            all_comparators[:-1], all_comparators[1:], node.ops
        ):
            compare_values.append(
                Compare(left=comparator_left, ops=[op], comparators=[comparator_right])
            )
        new_node = BoolOp(
            op=And(),
            values=compare_values,
        )
        return self.generic_visit(new_node)
