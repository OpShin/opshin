from ast import *

from ..util import CompilingNodeTransformer
from ..typed_ast import (
    TypedFunctionDef,
    FunctionType,
    NoneInstanceType,
    TypedConstant,
    RawPlutoExpr,
    InstanceType,
)

"""
Rewrites all functions that don't take arguments
into functions that take a singleton None argument.

Also rewrites all function calls without arguments
to calls that pass Unit into the function.
We need to take case of the dataclass call there, which should not be adjusted.
"""


class RewriteZeroAry(CompilingNodeTransformer):
    step = "Rewriting augmenting assignments"

    def visit_FunctionDef(self, node: TypedFunctionDef) -> TypedFunctionDef:
        if len(node.args.args) == 0:
            node.args.args.append(arg("_", Constant(None)))
            assert isinstance(node.typ.typ, FunctionType)
            node.typ.typ.argtyps.append(NoneInstanceType)
        self.generic_visit(node)
        return node
