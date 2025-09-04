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
