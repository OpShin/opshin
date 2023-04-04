from copy import copy

import typing
from ast import *

from ..util import CompilingNodeTransformer

"""
Rewrites all occurences of assignments to tuples to assignments to single values
"""


class RewriteTupleAssign(CompilingNodeTransformer):
    step = "Rewriting tuple deconstruction in assignments"

    unique_id = 0

    def visit_Assign(self, node: Assign) -> typing.List[stmt]:
        if not isinstance(node.targets[0], Tuple):
            return [node]
        uid = self.unique_id
        self.unique_id += 1
        assignments = [Assign([Name(f"{uid}_tup", Store())], self.visit(node.value))]
        for i, t in enumerate(node.targets[0].elts):
            assignments.append(
                Assign(
                    [t],
                    Subscript(
                        value=Name(f"{uid}_tup", Load()),
                        slice=Constant(i),
                        ctx=Load(),
                    ),
                )
            )
        # recursively resolve multiple layers of tuples
        transformed = sum([self.visit(a) for a in assignments], [])
        return transformed

    def visit_For(self, node: For) -> For:
        # rewrite deconstruction in for loops
        if not isinstance(node.target, Tuple):
            return self.generic_visit(node)
        new_for = copy(node)
        new_for.iter = self.visit(node.iter)
        uid = self.unique_id
        self.unique_id += 1
        # write the tuple into a singleton variable
        new_for.target = Name(f"{uid}_tup", Store())
        assignments = []
        # iteratively assign the deconstructed parts to the original variable names
        for i, t in enumerate(node.target.elts):
            assignments.append(
                Assign(
                    [t],
                    Subscript(
                        value=Name(f"{uid}_tup", Load()),
                        slice=Constant(i),
                        ctx=Load(),
                    ),
                )
            )
        new_for.body = assignments + node.body
        # recursively resolve multiple layers of tuples
        # further layers should be handled by the normal tuple assignment though
        return self.visit(new_for)
