from ast import *

from ..util import CompilingNodeTransformer
from .optimize_remove_deadvars import SafeOperationVisitor

"""
Removes expressions that are safely side effect free in sequences of statements
(e.g. constants, lambdas, string comments)
"""


class OptimizeRemoveDeadConstants(CompilingNodeTransformer):
    step = "Removing dead expressions"

    def visit_Expr(self, node: Expr):
        if SafeOperationVisitor([]).visit(node.value):
            return None
        return node
