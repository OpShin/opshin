from ast import *

from ..util import CompilingNodeTransformer
from ..typed_ast import (
    TypedFunctionDef,
    FunctionType,
    NoneInstanceType,
    TypedConstant,
    TypedCall,
    UnitInstanceType,
)

"""
Rewrites all functions that don't take arguments
into functions that take a singleton None argument.

Also rewrites all function calls without arguments
to calls that pass Unit into the function.
We need to take case of the dataclass call there, which should not be adjusted.
"""


class RewriteZeroAry(CompilingNodeTransformer):
    step = "Rewriting zero-ary functions"

    def visit_FunctionDef(self, node: TypedFunctionDef) -> TypedFunctionDef:
        if len(node.args.args) == 0:
            node.args.args.append(arg("_", Constant(None)))
            assert isinstance(node.typ.typ, FunctionType)
            node.typ.typ.argtyps.append(NoneInstanceType)
        self.generic_visit(node)
        return node

    def visit_Call(self, node: TypedCall) -> TypedCall:
        if isinstance(node.func, Name) and node.func.id == "dataclass":
            # special case for the dataclass function
            return node
        if node.func.typ.typ.argtyps == [UnitInstanceType] and node.args == []:
            # this would not pass the type check normally, only possible due to the zero-arg rewrite
            # 0-ary functions expect another parameter
            node.args.append(TypedConstant(None, typ=UnitInstanceType))
        self.generic_visit(node)
        return node
