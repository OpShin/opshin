from ..util import CompilingNodeTransformer
from ..typed_ast import *
import pluthon as plt

"""
Replaces empty dicts with UPLC constants of empty data pairs
"""


class RewriteEmptyDicts(CompilingNodeTransformer):
    step = "Rewrite empty lists to uplc empty lists"

    def visit_Dict(self, node: TypedDict):
        if node.keys or node.values:
            return node
        return RawPlutoExpr(typ=node.typ, expr=plt.MkNilPairData(plt.Unit()))

    def visit_Constant(self, node: TypedConstant):
        if node.value != {}:
            return node
        return RawPlutoExpr(typ=node.typ, expr=plt.MkNilPairData(plt.Unit()))
