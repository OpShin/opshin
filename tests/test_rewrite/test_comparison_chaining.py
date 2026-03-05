import hypothesis
from hypothesis import strategies as st

from tests.utils import eval_uplc_value, eval_uplc_raw

COMPARISON_OPS = ["<", "<=", "==", ">=", ">", "!="]


def _compare_python(a: int, op: str, b: int) -> bool:
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == "==":
        return a == b
    if op == ">=":
        return a >= b
    if op == ">":
        return a > b
    if op == "!=":
        return a != b
    raise ValueError(f"Unsupported comparison op: {op}")


@st.composite
def comparison_chain_case(draw):
    ops = draw(st.lists(st.sampled_from(COMPARISON_OPS), min_size=2, max_size=5))
    values = draw(
        st.lists(
            st.integers(min_value=-50, max_value=50),
            min_size=len(ops) + 1,
            max_size=len(ops) + 1,
        )
    )
    return values, ops


@hypothesis.given(
    st.lists(
        st.tuples(st.integers(), st.sampled_from(COMPARISON_OPS)),
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
        # middle expression in a comparison chain must be evaluated only once
        assert res.logs.count("hello") == 1
        assert bool(res.result.value) == (x < 5 < 10)


def test_comparison_chaining_short_circuits_later_operands():
    source_code = """

def foo(y: int) -> int:
    print("foo")
    return 5

def bar(y: int) -> int:
    print("bar")
    return 15

def validator(x: int) -> bool:
    return x < foo(x) < bar(x) < 20
"""

    # First comparison fails (10 < 5 is false): bar(x) must not be evaluated.
    res_false = eval_uplc_raw(source_code, 10)
    assert bool(res_false.result.value) is False
    assert res_false.logs.count("foo") == 1
    assert res_false.logs.count("bar") == 0

    # Full chain succeeds: each function is evaluated exactly once.
    res_true = eval_uplc_raw(source_code, 0)
    assert bool(res_true.result.value) is True
    assert res_true.logs.count("foo") == 1
    assert res_true.logs.count("bar") == 1


def test_comparison_chaining_mixed_operators_single_eval():
    source_code = """

def foo(y: int) -> int:
    print("foo")
    return 5

def bar(y: int) -> int:
    print("bar")
    return 8

def validator(x: int) -> bool:
    return x < foo(x) <= bar(x) != 9
"""

    res = eval_uplc_raw(source_code, 0)
    assert bool(res.result.value) is True
    assert res.logs.count("foo") == 1
    assert res.logs.count("bar") == 1


def test_comparison_chaining_mixed_operators_short_circuit_tail():
    source_code = """

def foo(y: int) -> int:
    print("foo")
    return 5

def bar(y: int) -> int:
    print("bar")
    return 4

def baz(y: int) -> int:
    print("baz")
    return 10

def validator(x: int) -> bool:
    return x < foo(x) <= bar(x) != baz(x)
"""

    # First link succeeds, second fails (5 <= 4 is false), so tail must not run.
    res = eval_uplc_raw(source_code, 0)
    assert bool(res.result.value) is False
    assert res.logs.count("foo") == 1
    assert res.logs.count("bar") == 1
    assert res.logs.count("baz") == 0


@hypothesis.given(case=comparison_chain_case())
@hypothesis.settings(max_examples=40, deadline=None)
@hypothesis.example(([2, 2, 3], ["==", "<"]))
def test_comparison_chaining_side_effect_eval_order(case):
    values, ops = case

    fn_defs = "\n\n".join(
        (f"def v{i}() -> int:\n" f'    print("v{i}")\n' f"    return {value}")
        for i, value in enumerate(values)
    )

    chain_expr = "v0()"
    for i, op in enumerate(ops, start=1):
        chain_expr += f" {op} v{i}()"

    source_code = f"""
{fn_defs}

def validator(_: int) -> bool:
    return {chain_expr}
"""

    res = eval_uplc_raw(source_code, 0)

    expected_result = True
    expected_evaluated = 1
    left = values[0]
    for i, op in enumerate(ops):
        right = values[i + 1]
        expected_evaluated += 1
        if not _compare_python(left, op, right):
            expected_result = False
            break
        left = right

    assert bool(res.result.value) == expected_result
    assert len(res.logs) == expected_evaluated
    assert sorted(res.logs) == [f"v{i}" for i in range(expected_evaluated)]


def test_comparison_single_op_dunder_override_still_supported():
    source_code = """
from typing import Self
from opshin.prelude import *

@dataclass()
class Foo(PlutusData):
    a: int

    def __le__(self, other: Self) -> bool:
        return self.a <= other.a

def validator(a: int, b: int) -> bool:
    return Foo(a) <= Foo(b)
"""

    for a, b in [(-5, -4), (0, 0), (7, 3)]:
        ret = eval_uplc_value(source_code, a, b)
        assert bool(ret) == (a <= b)


def test_comparison_multi_op_dunder_override_supported():
    source_code = """
from typing import Self
from opshin.prelude import *

@dataclass()
class Foo(PlutusData):
    a: int

    def __lt__(self, other: Self) -> bool:
        return self.a < other.a

def validator(a: int, b: int, c: int) -> bool:
    return Foo(a) < Foo(b) < Foo(c)
"""

    for a, b, c in [(-1, 0, 1), (3, 2, 1), (1, 1, 2), (4, 5, 5)]:
        ret = eval_uplc_value(source_code, a, b, c)
        assert bool(ret) == (a < b < c)
