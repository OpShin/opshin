from ast import *

from ..util import CompilingNodeTransformer

"""
Removes expressions that return constants in sequences of statements (i.e. string comments)
"""


class OptimizeRemoveDeadconstants(CompilingNodeTransformer):
    step = "Removing constants (i.e. string comments)"

    def visit_Expr(self, node: Expr):
        if isinstance(node.value, Constant):
            return None
        return node
