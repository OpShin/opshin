from ast import *

from ..util import CompilingNodeTransformer

"""
Rewrites all functions that don't take arguments
into functions that take a singleton None argument.

Also rewrites all function calls without arguments
to calls that pass Unit into the function.
We need to take case of the dataclass call there, which should not be adjusted.
"""


class RewriteZeroAry(CompilingNodeTransformer):
    step = "Rewriting augmenting assignments"

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        if len(node.args.args) == 0:
            node.args.args.append(arg("_", Constant(None)))
        self.generic_visit(node)
        return node

    def visit_Call(self, node: Call) -> Call:
        if len(node.args) == 0:
            node.args.append(Constant(None))
        self.generic_visit(node)
        return node
