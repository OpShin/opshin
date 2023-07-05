from copy import copy

from ast import *

from ..util import CompilingNodeTransformer

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
        return self.generic_visit(if_cp)

    def visit_IfExp(self, node: IfExp) -> IfExp:
        if_cp = copy(node)
        if_cp.test = Call(Name(SPECIAL_BOOL, Load()), [node.test], [])
        return self.generic_visit(if_cp)

    def visit_While(self, node: While) -> While:
        while_cp = copy(node)
        while_cp.test = Call(Name(SPECIAL_BOOL, Load()), [node.test], [])
        return self.generic_visit(while_cp)

    def visit_BoolOp(self, node: BoolOp) -> BoolOp:
        bo_cp = copy(node)
        bo_cp.values = [
            Call(Name(SPECIAL_BOOL, Load()), [self.visit(v)], []) for v in bo_cp.values
        ]
        return self.generic_visit(bo_cp)

    def visit_Assert(self, node: Assert) -> Assert:
        assert_cp = copy(node)
        assert_cp.test = Call(Name(SPECIAL_BOOL, Load()), [node.test], [])
        return self.generic_visit(assert_cp)
