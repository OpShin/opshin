from ast import *

from ..typed_ast import TypedCall, TypedAssert, TypedExpr
from ..fun_impls import PrintImpl
from ..type_impls import PolymorphicFunctionInstanceType
from ..util import CompilingNodeTransformer

"""
Removes traces in print and assert statements
"""


class OptimizeRemoveTrace(CompilingNodeTransformer):
    step = (
        "Removing occurrences of 'print' and 'assert', that use only constant strings"
    )

    def visit_Assert(self, node: TypedAssert):
        return TypedAssert(
            test=node.test,
            msg=None,
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

    def visit_Expr(self, node: TypedExpr):
        if isinstance(node.value, Call):
            node_call = node.value
            if (
                isinstance(node_call.func.typ, PolymorphicFunctionInstanceType)
                and isinstance(node_call.func.typ.polymorphic_function, PrintImpl)
                and all(isinstance(arg, Constant) for arg in node_call.args)
            ):
                return None
        return node
