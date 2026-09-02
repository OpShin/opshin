import ast
from copy import copy
from ast import *

from ..util import CompilingNodeTransformer
from ..typed_util import annotate_compound_statement_fallthrough
from .rewrite_cast_condition import SPECIAL_BOOL


class RewriteAnnotateFallthrough(CompilingNodeTransformer):
    step = "Annotating statement fallthrough"
    compound_statement_types = (Module, FunctionDef, ClassDef, If, For, While)

    @staticmethod
    def expr_is_definitely_false(node):
        if isinstance(node, Constant):
            return not bool(node.value)
        if (
            isinstance(node, Call)
            and isinstance(node.func, Name)
            and (node.func.id == SPECIAL_BOOL or node.func.orig_id == SPECIAL_BOOL)
            and len(node.args) == 1
            and not node.keywords
        ):
            return RewriteAnnotateFallthrough.expr_is_definitely_false(node.args[0])
        return False

    def generic_visit(self, node):
        if isinstance(node, self.compound_statement_types):
            node = copy(node)
        visited = super().generic_visit(node)
        if isinstance(visited, ast.stmt):
            visited.can_fall_through = getattr(visited, "can_fall_through", True)
        if isinstance(visited, self.compound_statement_types):
            return annotate_compound_statement_fallthrough(visited)
        return visited

    def visit_Return(self, node: Return) -> Return:
        return_cp = self.generic_visit(copy(node))
        return_cp.can_fall_through = False
        return return_cp

    def visit_Assert(self, node: Assert) -> Assert:
        assert_cp = self.generic_visit(copy(node))
        assert_cp.can_fall_through = not self.expr_is_definitely_false(assert_cp.test)
        return assert_cp
