from copy import copy

from ast import *

from ..util import CompilingNodeTransformer
from ..typed_ast import (
    TypedFunctionDef,
    FunctionType,
    NoneInstanceType,
    TypedConstant,
    TypedCall,
    UnitInstanceType,
)

"""
Rewrites all occurences of conditions to an implicit cast to bool
"""

SPECIAL_BOOL = "~bool"


class RewriteConditions(CompilingNodeTransformer):
    step = "Rewriting conditions to bools"

    def visit_Module(self, node: Module) -> Module:
        node.body.insert(0, Assign([Name(SPECIAL_BOOL, Store())], Name("bool", Load())))
        return self.generic_visit(node)

    def visit_If(self, node: If) -> If:
        if_cp = copy(node)
        if_cp.test = Call(Name(SPECIAL_BOOL, Load()), [node.test], [])
        return if_cp
