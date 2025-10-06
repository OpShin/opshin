import hypothesis.strategies as st
import pytest
from hypothesis import given

from opshin import CompilerError, builder
from tests.utils import eval_uplc_value


@pytest.mark.skip("Loops over tuples are not supported yet")
@given(st.integers())
def test_loop_over_tuple(x: int):
    source_code = """
def validator(x: int) -> int:
    t = (1, x)
    y = 0
    for x in t:
        y += x
    return y
"""
    assert eval_uplc_value(source_code, x) == 1 + x, (
        "Invalid implementation of loop over tuple"
    )


def test_loop_over_tuple_check():
    source_code = """
def validator(x: int) -> int:
    t = ("hi", x)
    y = 0
    for x in t:
        y += x
    return y
"""
    try:
        builder._compile(source_code)
        raise AssertionError("Should have raised SyntaxError")
    except CompilerError as e:
        assert "int" in str(e).lower() and "str" in str(e).lower(), (
            "Unexpected error message"
        )


@given(
    a=st.integers(min_value=-10, max_value=10),
    b=st.integers(min_value=0, max_value=10),
)
def test_mult_for_return(a: int, b: int):
    source_code = """
def validator(a: int, b: int) -> int:
    c = 0
    i = 0
    for i in range(b):
        c += a
        if i == 1:
            return c
    return c
"""
    ret = eval_uplc_value(source_code, a, b)
    assert ret == a * min(b, 2)


@given(
    a=st.integers(min_value=-10, max_value=10),
    b=st.integers(min_value=0, max_value=10),
)
def test_mult_while_return(a: int, b: int):
    source_code = """
def validator(a: int, b: int) -> int:
    c = 0
    i = 0
    while i < b:
        c += a
        i += 1
        if i == 2:
            return c
    return c
"""
    ret = eval_uplc_value(source_code, a, b)
    assert ret == a * min(2, b)
