import hypothesis
from hypothesis import strategies as st

from tests.utils import eval_uplc_value, eval_uplc_raw


@hypothesis.given(
    st.lists(
        st.tuples(st.integers(), st.sampled_from(["<", "<=", "==", ">=", ">", "!="])),
        max_size=10,
        min_size=2,
    )
)
@hypothesis.example(
    [
        (0, "<"),
        (0, "<"),
        (0, "<"),
        (0, "<"),
        (0, "<"),
        (0, "<"),
        (0, "<"),
        (0, "<"),
        (0, "<"),
        (0, "<"),
    ],
)
def test_comparison_chaining(xs):
    param_string = ",".join(f"i{k}: int" for k, _ in enumerate(xs))
    comp_string = "i0"
    eval_string = f"{xs[0][0]}"
    for k, (x, c) in enumerate(xs[1:], start=1):
        comp_string += f" {c} i{k}"
        eval_string += f" {c} {x}"
    source_code = f"""
def validator({param_string}) -> bool:
    return {comp_string}
"""
    res = eval_uplc_value(source_code, *[x[0] for x in xs])
    assert bool(res) == eval(eval_string)


def test_comparison_chaining_double_eval():
    source_code = """

def foo(y: int) -> int:
    print("hello")
    return 5

def validator(x: int) -> bool:
    return x < foo(x) < 10
"""
    for x in [0, 5, 10, 15]:
        res = eval_uplc_raw(source_code, x)
        assert res.logs.count("hello") == 1
        assert bool(res.result.value) == (x < 5 < 10)


def test_comparison_chaining_short_circuit_late_operand():
    source_code = """

def foo(y: int) -> int:
    print("foo")
    return 5

def bar() -> int:
    print("bar")
    return 10

def validator(x: int) -> bool:
    return x < foo(x) < bar()
"""
    res = eval_uplc_raw(source_code, 10)
    assert bool(res.result.value) is False
    assert res.logs.count("foo") == 1
    assert res.logs.count("bar") == 0

    res = eval_uplc_raw(source_code, 0)
    assert bool(res.result.value) is True
    assert res.logs.count("foo") == 1
    assert res.logs.count("bar") == 1


def test_comparison_chaining_dunder_once():
    source_code = """
from typing import Self
from opshin.prelude import *

@dataclass()
class Foo(PlutusData):
    a: int

    def __lt__(self, other: Self) -> bool:
        print("cmp")
        return self.a < other.a

def mk(x: int) -> Foo:
    print("mk")
    return Foo(x)

def validator(x: int, y: int, z: int) -> bool:
    return mk(x) < mk(y) < mk(z)
"""
    res = eval_uplc_raw(source_code, 0, 1, 2)
    assert bool(res.result.value) is True
    assert res.logs.count("mk") == 3
    assert res.logs.count("cmp") == 2

    res = eval_uplc_raw(source_code, 2, 1, 0)
    assert bool(res.result.value) is False
    assert res.logs.count("mk") == 2
    assert res.logs.count("cmp") == 1
