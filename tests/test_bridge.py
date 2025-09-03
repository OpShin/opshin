from typing import List, Dict

import hypothesis
from hypothesis import strategies as st

from opshin.bridge import wraps_builtin
from tests.utils import eval_uplc_value


@hypothesis.given(st.integers(), st.integers())
def test_bridge_add_int(a, b):
    @wraps_builtin
    def add_integer(x: int, y: int) -> int:
        pass

    assert add_integer(a, b) == a + b


@hypothesis.given(st.binary(), st.binary())
def test_bridge_add_bytes(a, b):
    @wraps_builtin
    def append_byte_string(x: bytes, y: bytes) -> bytes:
        pass

    assert append_byte_string(a, b) == a + b


@hypothesis.given(st.text(), st.text())
def test_bridge_add_strings(a, b):
    @wraps_builtin
    def append_string(x: str, y: str) -> str:
        pass

    assert append_string(a, b) == a + b


@hypothesis.given(st.lists(st.integers(), min_size=1))
def test_head_list(lst):
    @wraps_builtin
    def head_list(x: List[int]) -> int:
        pass

    assert head_list(lst) == lst[0]


@hypothesis.given(st.integers(), st.integers())
def test_bridge_add_int_uplc(a, b):
    code = """
from opshin.bridge import wraps_builtin

@wraps_builtin
def add_integer(x: int, y: int) -> int:
    pass

def validator(x: int, y: int) -> int:
    return add_integer(x, y)
    """
    value = eval_uplc_value(code, a, b)

    assert value == a + b


@hypothesis.given(st.binary(), st.binary())
def test_bridge_add_bytes_uplc(a, b):
    code = """
from opshin.bridge import wraps_builtin

@wraps_builtin
def append_byte_string(x: bytes, y: bytes) -> bytes:
    pass
    
def validator(x: bytes, y: bytes) -> bytes:
    return append_byte_string(x, y)
    """
    value = eval_uplc_value(code, a, b)
    assert value == a + b


@hypothesis.given(st.text(), st.text())
def test_bridge_add_strings_uplc(a: str, b: str):
    code = """
from opshin.bridge import wraps_builtin

@wraps_builtin
def append_string(x: str, y: str) -> str:
    pass
    
def validator(x: str, y: str) -> str:
    return append_string(x, y)
    """
    value = eval_uplc_value(code, a.encode(), b.encode()).decode()
    assert value == a + b


@hypothesis.given(st.lists(st.integers(), min_size=1))
def test_head_list_uplc(lst: List[int]):
    code = """
from opshin.bridge import wraps_builtin
from typing import Dict, List, Union

@wraps_builtin
def head_list(x: List[int]) -> int:
    pass
    
def validator(x: List[int]) -> int:
    return head_list(x)
    """
    value = eval_uplc_value(code, lst)
    assert value == lst[0]
