import pytest

from opshin import CompilerError, builder
from tests.utils import eval_uplc_value, eval_uplc


def test_error_message_list_no_import():
    source_code = """
def validator(x: List[int]) -> None:
    assert isinstance(x[0], int)
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
    with pytest.raises(RuntimeError, match="Execution") as e:
        eval_uplc(source_code, b"hi")


def test_import_mix():
    source_code = """
from typing import Dict, List
def validator(x: Dict[int, int], y: List[bytes]) -> None:
    assert isinstance(x[0], int)
        """
    eval_uplc(source_code, {1: 1, 2: 0, 0: 1}, [b"hi"])


def test_error_message_cast_no_import():
    source_code = """
def validator(x: int) -> int:
    return cast(int, x)
        """
    with pytest.raises(CompilerError, match="not imported") as e:
        builder._compile(source_code)


def test_cast_int_to_int():
    source_code = """
from typing import cast
def validator(x: int) -> int:
    return cast(int, x)
        """
    assert eval_uplc_value(source_code, 42) == 42


def test_cast_anything_to_int():
    source_code = """
from typing import cast
from pycardano import Datum as Anything
def validator(x: Anything) -> int:
    y = cast(int, x)
    return y + 1
        """
    assert eval_uplc_value(source_code, 41) == 42


def test_cast_int_to_anything():
    source_code = """
from typing import cast
from pycardano import Datum as Anything
def validator(x: int) -> Anything:
    return cast(Anything, x)
        """
    assert eval_uplc_value(source_code, 42) == 42


def test_cast_int_to_str_fails():
    # This should not compile - int and str are unrelated types
    source_code = """
from typing import cast
def validator(x: int) -> str:
    return cast(str, x)
        """
    with pytest.raises(CompilerError, match="Cannot cast") as e:
        builder._compile(source_code)
