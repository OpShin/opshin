from ast import *

from ..util import CompilingNodeTransformer
from .optimize_remove_deadvars import SafeOperationVisitor

"""
Removes expressions that are safely side effect free in sequences of statements
(e.g. constants, names, lambdas, string comments)
"""


class OptimizeRemoveDeadConstants(CompilingNodeTransformer):
    step = "Removing dead expressions"

    def visit_Expr(self, node: Expr):
        # After type-checking, all Name references are valid, so they are also side-effect-free
        if isinstance(node.value, Name) or SafeOperationVisitor([]).visit(node.value):
            return None
        return node
