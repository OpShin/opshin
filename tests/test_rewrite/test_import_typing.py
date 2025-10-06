import pytest

from opshin import CompilerError, builder
from tests.utils import eval_uplc


def test_error_message_list_no_import():
    source_code = """
def validator(x: List[int]) -> None:
    assert isinstance(x[0], int)
        """
    with pytest.raises(CompilerError, match="not imported"):
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
    with pytest.raises(CompilerError, match="not imported"):
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
    with pytest.raises(CompilerError, match="not imported"):
        builder._compile(source_code)


def test_import_just_list():
    source_code = """
from typing import List
def validator(x: List[int]) -> None:
    assert isinstance(x[0], int)
        """
    eval_uplc(source_code, [1, 2, 3])


def test_import_just_dict():
    source_code = """
from typing import Dict
def validator(x: Dict[int, int]) -> None:
    assert isinstance(x[0], int)
        """
    eval_uplc(source_code, {1: 1, 2: 0, 0: 1})


def test_import_just_union():
    source_code = """
from typing import Union
def validator(x: Union[int, bytes]) -> None:
    assert isinstance(x, int)
        """
    eval_uplc(source_code, 1)
    with pytest.raises(RuntimeError, match="Execution"):
        eval_uplc(source_code, b"hi")


def test_import_mix():
    source_code = """
from typing import Dict, List
def validator(x: Dict[int, int], y: List[bytes]) -> None:
    assert isinstance(x[0], int)
        """
    eval_uplc(source_code, {1: 1, 2: 0, 0: 1}, [b"hi"])
