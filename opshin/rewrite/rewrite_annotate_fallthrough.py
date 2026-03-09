import ast
from copy import copy
from ast import *

from ..util import CompilingNodeTransformer
from ..typed_util import annotate_compound_statement_fallthrough
from .rewrite_cast_condition import SPECIAL_BOOL


class RewriteAnnotateFallthrough(CompilingNodeTransformer):
    step = "Annotating statement fallthrough"

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
        visited = super().generic_visit(node)
        if isinstance(visited, ast.stmt):
            visited.can_fall_through = getattr(visited, "can_fall_through", True)
        return visited

    def visit_Module(self, node: Module) -> Module:
        module_cp = self.generic_visit(copy(node))
        return annotate_compound_statement_fallthrough(module_cp)

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        func_cp = self.generic_visit(copy(node))
        return annotate_compound_statement_fallthrough(func_cp)

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        class_cp = self.generic_visit(copy(node))
        return annotate_compound_statement_fallthrough(class_cp)

    def visit_If(self, node: If) -> If:
        if_cp = self.generic_visit(copy(node))
        return annotate_compound_statement_fallthrough(if_cp)

    def visit_For(self, node: For) -> For:
        for_cp = self.generic_visit(copy(node))
        return annotate_compound_statement_fallthrough(for_cp)

    def visit_While(self, node: While) -> While:
        while_cp = self.generic_visit(copy(node))
        return annotate_compound_statement_fallthrough(while_cp)

    def visit_Return(self, node: Return) -> Return:
        return_cp = self.generic_visit(copy(node))
        return_cp.can_fall_through = False
        return return_cp

    def visit_Assert(self, node: Assert) -> Assert:
        assert_cp = self.generic_visit(copy(node))
        assert_cp.can_fall_through = not self.expr_is_definitely_false(assert_cp.test)
        return assert_cp
