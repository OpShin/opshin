from copy import copy

from .typed_ast import *
from .util import PythonBuiltIn, PythonBuiltInTypes, RawPlutoExpr

import pluthon as plt

"""
Inject initialising the builtin functions
"""


class RewriteInjectBuiltins(NodeTransformer):
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
