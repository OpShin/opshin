import ast
from copy import copy
from ast import *

from ..util import CompilingNodeTransformer
from .rewrite_cast_condition import SPECIAL_BOOL


class RewriteAnnotateFallthrough(CompilingNodeTransformer):
    step = "Annotating statement fallthrough"

    @staticmethod
    def sequence_can_fall_through(nodes):
        for node in nodes:
            if not getattr(node, "can_fall_through", True):
                return False
        return True

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
        module_cp.can_fall_through = self.sequence_can_fall_through(module_cp.body)
        return module_cp

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        func_cp = self.generic_visit(copy(node))
        func_cp.body_can_fall_through = self.sequence_can_fall_through(func_cp.body)
        func_cp.can_fall_through = True
        return func_cp

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        class_cp = self.generic_visit(copy(node))
        class_cp.body_can_fall_through = self.sequence_can_fall_through(class_cp.body)
        class_cp.can_fall_through = True
        return class_cp

    def visit_If(self, node: If) -> If:
        if_cp = self.generic_visit(copy(node))
        if_cp.body_can_fall_through = self.sequence_can_fall_through(if_cp.body)
        if_cp.orelse_can_fall_through = self.sequence_can_fall_through(if_cp.orelse)
        if_cp.can_fall_through = (
            if_cp.body_can_fall_through or if_cp.orelse_can_fall_through
        )
        return if_cp

    def visit_For(self, node: For) -> For:
        for_cp = self.generic_visit(copy(node))
        for_cp.body_can_fall_through = self.sequence_can_fall_through(for_cp.body)
        for_cp.orelse_can_fall_through = self.sequence_can_fall_through(for_cp.orelse)
        # Without break support, normal loop completion always enters the else branch.
        for_cp.can_fall_through = for_cp.orelse_can_fall_through
        return for_cp

    def visit_While(self, node: While) -> While:
        while_cp = self.generic_visit(copy(node))
        while_cp.body_can_fall_through = self.sequence_can_fall_through(while_cp.body)
        while_cp.orelse_can_fall_through = self.sequence_can_fall_through(
            while_cp.orelse
        )
        # Without break support, normal loop completion always enters the else branch.
        while_cp.can_fall_through = while_cp.orelse_can_fall_through
        return while_cp

    def visit_Return(self, node: Return) -> Return:
        return_cp = self.generic_visit(copy(node))
        return_cp.can_fall_through = False
        return return_cp

    def visit_Assert(self, node: Assert) -> Assert:
        assert_cp = self.generic_visit(copy(node))
        assert_cp.can_fall_through = not self.expr_is_definitely_false(assert_cp.test)
        return assert_cp
