from ast import *
import typing

"""
Rewrites all occurences of For-loops into equivalent While-loops
"""

class RewriteFor(NodeTransformer):

    unique_id = 0

    def visit_For(self, node: For) -> typing.List[stmt]:
        uid = self.unique_id
        self.unique_id += 1
        prelude = [
            Assign(
                [
                    Tuple([
                        Name(f"__initialstate{uid}__", Store()),
                        Name(f"__iterfun{uid}__", Store()),
                    ], Store()),
                ],
                node.iter,
            ),
            Assign(
                [
                    Tuple([
                        Name(f"__isvalid{uid}__", Store()),
                        Name(f"__curval{uid}__", Store()),
                        Name(f"__curstate{uid}__", Store()),
                    ], Store()),
                ],
                Call(Name(f"__iterfun{uid}__", Load()), [Name(f"__initialstate{uid}__", Load())], []),
            ),
        ]
        w = While(
            test=Compare(Name(f"__isvalid{uid}__", Load()), [Eq()], [Constant(True)]),
            body=[Assign([node.target], Name(f"__curval{uid}__", Load()))] + [self.visit(n) for n in node.body],
            orelse=[self.visit(n) for n in node.orelse],
        )
        return prelude + [w]