"""Rewrite rule to prevent asserting None values."""

import ast
from typing import Optional, cast

from .rewrite_cast_condition import SPECIAL_BOOL
from ..typed_ast import TypedAssert
from ..type_impls import UnitInstanceType, InstanceType, UnitType
from ..util import CompilingNodeTransformer


class RewriteAssertNone(CompilingNodeTransformer):
    """Prevent asserting None values as this would always fail."""

    step = "Checking for assertions of None values"

    def visit_Assert(self, node: TypedAssert) -> Optional[ast.AST]:
        """Prevent asserting None values as this would always fail."""
        # Check if the test expression is a call that returns None
        if (
            isinstance(node.test, ast.Call)
            and hasattr(node.test, "typ")
            and (
                node.test.typ == UnitInstanceType
                or (
                    isinstance(node.test.typ, InstanceType)
                    and isinstance(node.test.typ.typ, UnitType)
                )
            )
        ):
            raise SyntaxError(
                f"Asserting a function call that returns None at line {node.lineno}. "
                "This would always fail as it's equivalent to 'assert False'. "
                "The function likely performs its own assertions internally."
            )

        return node
