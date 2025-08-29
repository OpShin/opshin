import pytest

from opshin import builder, CompilerError


def test_dataclass_function_overwrite():
    code = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union

# Custom dataclass decorator
def dataclass(cls: int) -> int:
    return cls

def validator(a: int) -> None:
    return None
"""
    with pytest.raises(CompilerError) as e:
        builder._compile(code)
    assert "ForbiddenOverwriteError" in str(e.value)


def test_dataclass_class_overwrite():
    code = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union

# Custom dataclass class
@dataclass
class dataclass(PlutusData):
    a: int


def validator(a: int) -> None:
    return None
"""
    with pytest.raises(CompilerError) as e:
        builder._compile(code)
    assert "ForbiddenOverwriteError" in str(e.value)
