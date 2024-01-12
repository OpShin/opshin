import re
from copy import copy
from typing import Optional
from enum import Enum

from ..util import CompilingNodeTransformer
from ..typed_ast import *

"""
Replaces empty lists with UPLC constants of empty lists
"""


class RewriteEmptyLists(CompilingNodeTransformer):
    step = "Rewrite empty lists to uplc empty lists"

    def visit_List(self, node: TypedList):
        if node.elts:
            return node
        return RawPlutoExpr(typ=node.typ, expr=empty_list(node.typ.typ.typ))

    def visit_Constant(self, node: TypedConstant):
        if node.value != []:
            return node
        return RawPlutoExpr(typ=node.typ, expr=empty_list(node.typ.typ.typ))
