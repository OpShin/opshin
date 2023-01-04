from ast import *
import typing

"""
Rewrites all occurences of assignments to tuples to assignments to single values
"""


class RewriteTupleAssign(NodeTransformer):

    unique_id = 0

    def visit_Assign(self, node: Assign) -> typing.List[stmt]:
        if not isinstance(node.targets[0], Tuple):
            return [node]
        uid = self.unique_id
        self.unique_id += 1
        assignments = [
            Assign([Name(f"__tuple{uid}__", Store())], self.visit(node.value))
        ]
        for i, t in enumerate(node.targets[0].elts):
            assignments.append(
                Assign(
                    [t],
                    Subscript(
                        value=Name(f"__tuple{uid}__", Load()),
                        slice=Index(value=Constant(i)),
                        ctx=Load(),
                    ),
                )
            )
        # recursively resolve multiple layers of tuples
        transformed = sum([self.visit(a) for a in assignments], [])
        return transformed
