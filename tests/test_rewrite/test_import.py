import pytest

from opshin import builder
from opshin.util import CompilerError


def test_import_without_from():
    source_code = """
import opshin.prelude

def validator(a: int) -> int:
    return opshin.prelude.add(a, 1)
    """
    try:
        builder._compile(source_code)
        assert False, "Expected compilation failure due to import without from"
    except CompilerError as e:
        assert "import" in str(e).lower(), "Unexpected error message"


def test_import_without_from_with_as():
    source_code = """
import opshin.prelude as prelude

def validator(a: int) -> int:
    return prelude.add(a, 1)
    """
    try:
        builder._compile(source_code)
        assert False, "Expected compilation failure due to import without from"
    except CompilerError as e:
        assert "import" in str(e).lower(), "Unexpected error message"


def test_import_style_invalid():
    source_code = """
import opshin.prelude
def validator(a: int) -> int:
    return a + 1
    """
    with pytest.raises(CompilerError) as e:
        builder._compile(source_code)
    assert "import must have the form" in str(e).lower(), "Unexpected error message"


def test_import_invalid_module():
    source_code = """
from non_existent_module import *
def validator(a: int) -> int:
    return a + 1
    """
    with pytest.raises(CompilerError) as e:
        builder._compile(source_code)
    assert "non_existent_module" in str(e).lower(), "Unexpected error message"
    assert "no module named" in str(e).lower(), "Unexpected error message"


def test_selective_import_valid():
    """Test that selective imports work correctly"""
    # Create a test module content in memory
    test_module_code = """
def function_a(x: int) -> int:
    return x + 1

def function_b(x: int) -> int:
    return x * 2

variable_a: int = 10
variable_b: int = 20
"""

    # Write test module to file
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_module_code)
        test_module_path = f.name

    try:
        # Get the module name from path
        module_name = os.path.splitext(os.path.basename(test_module_path))[0]
        module_dir = os.path.dirname(test_module_path)

        # Add the module to sys.path manually for the test
        import sys

        sys.path.append(module_dir)

        try:
            source_code = f"""
from {module_name} import function_a, variable_a

def validator(x: int) -> int:
    return function_a(x) + variable_a
"""

            # This should compile successfully
            result = builder._compile(source_code)
            assert result is not None, "Selective import should compile successfully"

        finally:
            # Clean up sys.path
            if module_dir in sys.path:
                sys.path.remove(module_dir)

    finally:
        os.unlink(test_module_path)


def test_selective_import_error():
    """Test that using non-imported names fails"""
    # Create a test module content in memory
    test_module_code = """
def function_a(x: int) -> int:
    return x + 1

def function_b(x: int) -> int:
    return x * 2

variable_a: int = 10
"""

    # Write test module to file
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_module_code)
        test_module_path = f.name

    try:
        # Get the module name from path
        module_name = os.path.splitext(os.path.basename(test_module_path))[0]
        module_dir = os.path.dirname(test_module_path)

        # Add the module to sys.path manually for the test
        import sys

        sys.path.append(module_dir)

        try:
            source_code = f"""
from {module_name} import function_a

def validator(x: int) -> int:
    return function_a(x) + function_b(x)  # function_b not imported
"""

            # This should fail to compile
            with pytest.raises(CompilerError) as e:
                builder._compile(source_code)
            assert "function_b" in str(
                e
            ), "Should fail because function_b was not imported"

        finally:
            # Clean up sys.path
            if module_dir in sys.path:
                sys.path.remove(module_dir)

    finally:
        os.unlink(test_module_path)
