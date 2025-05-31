from copy import copy

from ast import *

from ..util import CompilingNodeTransformer

"""
Rewrites all occurences of conditions to an implicit cast to bool
"""

SPECIAL_BOOL = "~bool"


class RewriteConditions(CompilingNodeTransformer):
    step = "Rewriting conditions to bools"

    def __init__(self):
        super().__init__()
        self.function_defs = {}  # Store function definitions for lookup

    def visit_Module(self, node: Module) -> Module:
        # First pass: collect all function definitions
        for item in node.body:
            if isinstance(item, FunctionDef):
                self.function_defs[item.name] = item

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
        # Check for dangerous pattern: assert function_call() where function returns None
        if isinstance(node.test, Call) and isinstance(node.test.func, Name):
            func_name = node.test.func.id
            if func_name in self.function_defs:
                func_def = self.function_defs[func_name]
                # Check if the function has a return annotation of None
                if func_def.returns is not None and (
                    (
                        isinstance(func_def.returns, Constant)
                        and func_def.returns.value is None
                    )
                    or (
                        isinstance(func_def.returns, Name)
                        and func_def.returns.id == "None"
                    )
                ):
                    raise SyntaxError(
                        f"Asserting a function call that returns None at line {node.lineno}. "
                        f"Function '{func_name}' returns None, so 'assert {func_name}(...)' "
                        "would always fail as it's equivalent to 'assert False'. "
                        "The function likely performs its own assertions internally."
                    )

        assert_cp = copy(node)
        assert_cp.test = Call(Name(SPECIAL_BOOL, Load()), [node.test], [])
        return self.generic_visit(assert_cp)
