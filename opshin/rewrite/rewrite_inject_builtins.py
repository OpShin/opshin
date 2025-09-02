from copy import copy, deepcopy
import pluthon as plt
import ast

from ..typed_ast import *
from ..util import (
    CompilingNodeTransformer,
    force_params,
)
from ..fun_impls import PythonBuiltIn, PythonBuiltInTypes

"""
Inject initialising the builtin functions
"""


class RewriteInjectBuiltins(CompilingNodeTransformer):
    step = "Injecting builtin functions"

    def visit_Module(self, node: TypedModule) -> TypedModule:
        additional_assigns = []
        for b in PythonBuiltIn:
            typ = PythonBuiltInTypes[b]
            if not isinstance(b.value, plt.AST):
                # skip polymorphic functions
                continue
            additional_assigns.append(
                ast.Assign(
                    targets=[ast.Name(id=b.name, typ=typ, ctx=ast.Store())],
                    value=RawPlutoExpr(typ=typ, expr=force_params(deepcopy(b.value))),
                )
            )
        md = copy(node)
        # prepend all builtin definitions
        md.body = additional_assigns + node.body
        return md
