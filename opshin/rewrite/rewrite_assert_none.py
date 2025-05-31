"""Rewrite rule to prevent asserting None values."""

import ast
from typing import Optional, cast

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

        # Also check if this is a call to a function that has a None return type annotation
        if isinstance(node.test, ast.Call) and isinstance(node.test.func, ast.Name):
            print(f"DEBUG: Function call to {node.test.func.id}")
            print(f"DEBUG: func has typ: {hasattr(node.test.func, 'typ')}")
            if hasattr(node.test.func, "typ"):
                print(f"DEBUG: func.typ: {node.test.func.typ}")
                print(f"DEBUG: func.typ has typ: {hasattr(node.test.func.typ, 'typ')}")
                if hasattr(node.test.func.typ, "typ"):
                    print(f"DEBUG: func.typ.typ: {node.test.func.typ.typ}")
                    print(
                        f"DEBUG: func.typ.typ has rettyp: {hasattr(node.test.func.typ.typ, 'rettyp')}"
                    )
                    if hasattr(node.test.func.typ.typ, "rettyp"):
                        print(
                            f"DEBUG: func.typ.typ.rettyp: {node.test.func.typ.typ.rettyp}"
                        )

        if (
            isinstance(node.test, ast.Call)
            and isinstance(node.test.func, ast.Name)
            and hasattr(node.test.func, "typ")
            and hasattr(node.test.func.typ, "typ")
            and hasattr(node.test.func.typ.typ, "rettyp")
            and (
                node.test.func.typ.typ.rettyp == UnitInstanceType
                or (
                    isinstance(node.test.func.typ.typ.rettyp, InstanceType)
                    and isinstance(node.test.func.typ.typ.rettyp.typ, UnitType)
                )
            )
        ):
            raise SyntaxError(
                f"Asserting a function call that returns None at line {node.lineno}. "
                "This would always fail as it's equivalent to 'assert False'. "
                "The function likely performs its own assertions internally."
            )

        return node
