from ast import *

from opshin.util import CompilingNodeTransformer
from opshin.rewrite.rewrite_cast_condition import SPECIAL_BOOL
from opshin.type_impls import BoolType, InstanceType

"""
Pre-evaluates ~bool to constants
"""


class OptimizeFoldBoolCast(CompilingNodeTransformer):
    step = "Removing ~bool calls to constants"

    def visit_Call(self, node: Call) -> Call:
        if isinstance(node.func, Name) and node.func.orig_id == SPECIAL_BOOL:
            if len(node.args) != 1:
                return self.generic_visit(node)
            arg = self.visit(node.args[0])
            if isinstance(arg.typ, InstanceType) and isinstance(arg.typ.typ, BoolType):
                return arg
        return self.generic_visit(node)
