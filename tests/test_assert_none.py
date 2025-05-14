import ast
import pytest
import sys
from typing import Optional

from opshin import builder
from opshin.typed_ast import TypedAssert
from opshin.rewrite.rewrite_assert_none import RewriteAssertNone


def test_assert_none():
    """Test that asserting None values raises a SyntaxError."""
    # Create a test AST node
    test_node = TypedAssert(
        test=ast.Call(
            func=ast.Name(id="foo_test", ctx=ast.Load()),
            args=[ast.Constant(value=1)],
            keywords=[],
            typ="NoneType",
        ),
        msg=None,
        lineno=1,
        col_offset=0,
    )

    # Create the rewrite rule
    rewrite = RewriteAssertNone()

    # Test that it raises a SyntaxError
    with pytest.raises(SyntaxError) as excinfo:
        rewrite.visit_Assert(test_node)

    assert "Asserting a function call that returns None" in str(excinfo.value)


def test_valid_assert():
    """Test that valid assertions are not affected."""
    # Create a test AST node
    test_node = TypedAssert(
        test=ast.Call(
            func=ast.Name(id="foo_test", ctx=ast.Load()),
            args=[ast.Constant(value=1)],
            keywords=[],
            typ="bool",  # Return type is bool, not None
        ),
        msg=None,
        lineno=1,
        col_offset=0,
    )

    # Create the rewrite rule
    rewrite = RewriteAssertNone()

    # Test that it doesn't raise a SyntaxError
    result = rewrite.visit_Assert(test_node)

    # The node should be returned unchanged
    assert result is test_node


def test_non_call_assert():
    """Test that assertions of non-call expressions are not affected."""
    # Create a test AST node with a simple boolean expression
    test_node = TypedAssert(
        test=ast.Compare(
            left=ast.Constant(value=1),
            ops=[ast.Eq()],
            comparators=[ast.Constant(value=1)],
            typ="bool",
        ),
        msg=None,
        lineno=1,
        col_offset=0,
    )

    # Create the rewrite rule
    rewrite = RewriteAssertNone()

    # Test that it doesn't raise a SyntaxError
    result = rewrite.visit_Assert(test_node)

    # The node should be returned unchanged
    assert result is test_node


def test_assert_none_call():
    """Test that asserting None values raises a SyntaxError."""
    code = """
def foo_test(x: int) -> None:
    assert 1 == x
  
def validator(x: int) -> bool:
    assert foo_test(x)  # always (unintentionally) fails
    return True
"""

    # Test that it raises a SyntaxError
    with pytest.raises(SyntaxError) as excinfo:
        builder._compile(code)

    assert "Asserting a function call that returns None" in str(excinfo.value)
