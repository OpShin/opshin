"""Rewrite rule to prevent asserting None values."""

import ast
from typing import Optional, cast

from ..typed_ast import TypedAssert
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
            and str(node.test.typ) == "NoneType"
        ):
            raise SyntaxError(
                f"Asserting a function call that returns None at line {node.lineno}. "
                "This would always fail as it's equivalent to 'assert False'. "
                "The function likely performs its own assertions internally."
            )

        return node
