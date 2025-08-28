from ast import *
from copy import deepcopy

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
            # Deep copy comparators to avoid sharing AST nodes between comparisons
            # This prevents scoping issues when the same expression appears multiple times
            compare_values.append(
                Compare(
                    left=deepcopy(comparator_left),
                    ops=[op],
                    comparators=[deepcopy(comparator_right)],
                )
            )
        new_node = BoolOp(
            op=And(),
            values=compare_values,
        )
        return self.generic_visit(new_node)
