from __future__ import annotations
from copy import copy
from dataclasses import dataclass

import typing
from ast import *

from ..util import CompilingNodeTransformer

"""
Rewrites all occurrences of assignments to tuples to assignments to single values
"""


@dataclass(frozen=True)
class DestructureMetadata:
    kind: str
    length: typing.Optional[int] = None
    index: typing.Optional[int] = None


class RewriteTupleAssign(CompilingNodeTransformer):
    step = "Rewriting tuple deconstruction in assignments"

    unique_id = 0

    def visit_Assign(self, node: Assign) -> typing.List[stmt]:
        if not isinstance(node.targets[0], Tuple):
            return [node]
        uid = self.unique_id
        self.unique_id += 1
        tuple = self.visit(node.value)
        # store for later that we require
        tuple.is_tuple_with_deconstruction = len(node.targets[0].elts)
        temp_name = f"2_{uid}_tup"
        temp_assignment = Assign([Name(temp_name, Store())], tuple)
        temp_assignment.destructure_metadata = DestructureMetadata(
            kind="assignment",
            length=len(node.targets[0].elts),
        )
        assignments = [temp_assignment]
        for i, t in enumerate(node.targets[0].elts):
            assignment = Assign(
                [t],
                Subscript(
                    value=Name(temp_name, Load()),
                    slice=Constant(i),
                    ctx=Load(),
                ),
            )
            assignment.destructure_metadata = DestructureMetadata(
                kind="extraction",
                index=i,
            )
            assignments.append(assignment)
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
        new_for.target = Name(f"2_{uid}_tup", Store())
        assignments = []
        # TODO for now we only have lists over pairs, so we can just check length = 2
        # in the future need to handle as above
        if len(node.target.elts) < 2:
            raise ValueError(
                f"Too many values to unpack in for loop target, expected 2, got {len(node.target.elts)}"
            )
        if len(node.target.elts) > 2:
            raise ValueError(
                f"Not enough values to unpack in for loop target, expected 2, got {len(node.target.elts)}"
            )
        # iteratively assign the deconstructed parts to the original variable names
        for i, t in enumerate(node.target.elts):
            assignments.append(
                Assign(
                    [t],
                    Subscript(
                        value=Name(f"2_{uid}_tup", Load()),
                        slice=Constant(i),
                        ctx=Load(),
                    ),
                )
            )
        new_for.body = assignments + node.body
        # recursively resolve multiple layers of tuples
        # further layers should be handled by the normal tuple assignment though
        return self.visit(new_for)
