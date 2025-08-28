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
        res = eval_uplc_raw(source_code, 1)
        # inspect the logs to check that foo() is only called once
        assert res.logs.count("hello") == 1
        assert bool(res.result) == x < 5 < 10
