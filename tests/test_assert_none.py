import ast
import pytest
import sys
from typing import Optional

from opshin import builder
from opshin.util import CompilerError


def test_assert_none_call():
    """Test that asserting None values raises a SyntaxError."""
    code = """
def foo_test(x: int) -> None:
    assert 1 == x
  
def validator(x: int) -> bool:
    assert foo_test(x)  # always (unintentionally) fails
    return True
"""

    # Test that it raises a CompilerError wrapping a SyntaxError
    with pytest.raises(CompilerError) as excinfo:
        builder._compile(code)

    # Check that the underlying error is a SyntaxError with the right message
    assert isinstance(excinfo.value.args[0], SyntaxError)
    assert "Asserting a function call that returns None" in str(excinfo.value.args[0])


def test_assert_none_nested_call():
    """Test that asserting nested function calls that return None raises a SyntaxError."""
    code = """
def validator(x: int) -> bool:
    def foo_test(y: int) -> None:
        assert 1 == y
    
    assert foo_test(x)  # always (unintentionally) fails
    return True
"""

    # Test that it raises a CompilerError wrapping a SyntaxError
    with pytest.raises(CompilerError) as excinfo:
        builder._compile(code)

    # Check that the underlying error is a SyntaxError with the right message
    assert isinstance(excinfo.value.args[0], SyntaxError)
    assert "Asserting a function call that returns None" in str(excinfo.value.args[0])
