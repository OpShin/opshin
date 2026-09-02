from copy import copy
from dataclasses import dataclass

import typing
from ast import *

from ..util import CompilingNodeTransformer, NameSupply

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

    def visit_Module(self, node: Module) -> Module:
        self.name_supply = NameSupply.from_tree(node, "tuple")
        return self.generic_visit(node)

    def visit_Assign(self, node: Assign) -> typing.List[stmt]:
        if not isinstance(node.targets[0], Tuple):
            return [node]
        tuple = self.visit(node.value)
        # store for later that we require
        tuple.is_tuple_with_deconstruction = len(node.targets[0].elts)
        temp_name = self.name_supply.fresh_name()
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
        temp_name = self.name_supply.fresh_name()
        # write the tuple into a singleton variable
        new_for.target = Name(temp_name, Store())
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
                        value=Name(temp_name, Load()),
                        slice=Constant(i),
                        ctx=Load(),
                    ),
                )
            )
        new_for.body = assignments + node.body
        # recursively resolve multiple layers of tuples
        # further layers should be handled by the normal tuple assignment though
        return self.visit(new_for)
