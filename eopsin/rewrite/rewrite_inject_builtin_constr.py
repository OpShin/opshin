from copy import copy

from ..typed_ast import *
from ..util import (
    CompilingNodeTransformer,
)

"""
Inject constructors for the builtin types that double function as type annotation
"""


class RewriteInjectBuiltinsConstr(CompilingNodeTransformer):
    step = "Injecting builtin type constructors"

    def visit_Module(self, node: TypedModule) -> TypedModule:
        additional_assigns = []
        for t, tname in [
            (ByteStringType(), bytes.__name__),
            (IntegerType(), int.__name__),
            (StringType(), str.__name__),
        ]:
            typ = t.constr_type()
            if isinstance(typ.typ, PolymorphicFunctionType):
                # skip polymorphic functions
                continue
            additional_assigns.append(
                TypedAssign(
                    targets=[TypedName(id=tname, typ=typ, ctx=Store())],
                    value=RawPlutoExpr(typ=typ, expr=plt.Lambda(["_"], t.constr())),
                )
            )
        md = copy(node)
        # prepend all builtin definitions
        md.body = additional_assigns + node.body
        return md
