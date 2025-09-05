import pytest

from opshin import CompilerError, builder


def test_error_message_list_no_import():
    source_code = """
def validator(x: List) -> None:
    assert isinstance(x, int)
        """
    with pytest.raises(CompilerError, match="not imported") as e:
        builder._compile(source_code)


def test_error_message_self_no_import():
    source_code = """
from typing import Dict, List, Union
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData

@dataclass
class A(PlutusData):
    foo: int
    
    def bar(self) -> Self:
        return self

def validator(x: A) -> None:
    assert isinstance(x, A)
        """
    with pytest.raises(CompilerError, match="not imported") as e:
        builder._compile(source_code)


def test_error_message_self_no_import_outside():
    source_code = """
from typing import Dict, List, Union
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData


def bar(self) -> Self:
    return self

def validator(x: A) -> None:
    assert isinstance(x, A)
        """
    with pytest.raises(CompilerError, match="not imported") as e:
        builder._compile(source_code)
