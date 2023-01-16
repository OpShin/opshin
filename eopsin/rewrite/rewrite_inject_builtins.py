from copy import copy

import pluthon as plt

from ..typed_ast import *
from ..util import PythonBuiltIn, PythonBuiltInTypes, RawPlutoExpr, TypedNodeTransformer

"""
Inject initialising the builtin functions
"""


class RewriteInjectBuiltins(TypedNodeTransformer):
    def visit_Module(self, node: TypedModule) -> TypedModule:
        additional_assigns = []
        for b in PythonBuiltIn:
            typ = PythonBuiltInTypes[b]
            additional_assigns.append(
                TypedAssign(
                    targets=[TypedName(id=b.name, typ=typ)],
                    value=RawPlutoExpr(typ=typ, expr=plt.Lambda(["_"], b.value)),
                )
            )
        md = copy(node)
        # prepend all builtin definitions
        md.body = additional_assigns + node.body
        return md
