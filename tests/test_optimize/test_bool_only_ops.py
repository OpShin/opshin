import pytest
import uplc
from hypothesis import given, strategies as st

from opshin import builder
from tests.utils import DEFAULT_TEST_CONFIG, eval_uplc_value


@pytest.mark.parametrize(
    "body",
    [
        "return bool(a {operator} b)",
        "if a {operator} b:\n        return True\n    return False",
        (
            "result = False\n"
            "    while a {operator} b:\n"
            "        result = True\n"
            "        a = 0\n"
            "        b = 0\n"
            "    return result"
        ),
    ],
)
@pytest.mark.parametrize("operator", ["and", "or"])
@given(a=st.sampled_from([0, 3]), b=st.sampled_from([0, 2]))
def test_bool_only_ops_are_cheaper_in_all_condition_contexts(body, operator, a, b):
    source_code = f"""
def validator(a: int, b: int) -> bool:
    {body.format(operator=operator)}
"""
    baseline_code = builder._compile(
        source_code,
        a,
        b,
        config=DEFAULT_TEST_CONFIG.update(optimize_bool_only_ops=False),
    )
    optimized_code = builder._compile(
        source_code,
        a,
        b,
        config=DEFAULT_TEST_CONFIG.update(optimize_bool_only_ops=True),
    )
    baseline = uplc.eval(baseline_code)
    optimized = uplc.eval(optimized_code)

    assert optimized.result == baseline.result
    assert len(uplc.flatten(optimized_code)) < len(uplc.flatten(baseline_code))
    assert optimized.cost.cpu < baseline.cost.cpu
    assert optimized.cost.memory < baseline.cost.memory


@pytest.mark.parametrize("operator", ["and", "or"])
@given(a=st.integers(), b=st.integers())
def test_bool_only_condition_preserves_behavior(operator, a, b):
    source_code = f"""
def validator(a: int, b: int) -> int:
    if a {operator} b:
        return 1
    return 0
"""
    result = eval_uplc_value(
        source_code,
        a,
        b,
        config=DEFAULT_TEST_CONFIG.update(optimize_bool_only_ops=True),
    )
    expected = (a and b) if operator == "and" else (a or b)
    assert result == int(bool(expected))


@pytest.mark.parametrize(
    "expression,args,expected",
    [
        ("bool(a and (10 // b))", (0, 0, 0), False),
        ("bool(a or (10 // b))", (1, 0, 0), True),
        ("bool((a and b) or c)", (3, 0, 2), True),
        ("bool((a or b) and c)", (0, 3, 2), True),
    ],
)
def test_bool_only_op_preserves_short_circuiting_and_nesting(
    expression, args, expected
):
    source_code = f"""
def validator(a: int, b: int, c: int) -> bool:
    return {expression}
"""
    result = eval_uplc_value(
        source_code,
        *args,
        config=DEFAULT_TEST_CONFIG.update(optimize_bool_only_ops=True),
    )
    assert bool(result) is expected


@pytest.mark.parametrize("operator", ["and", "or"])
@given(a=st.integers(), b=st.integers())
def test_value_preserving_bool_op_is_not_optimized(operator, a, b):
    source_code = f"""
def validator(a: int, b: int) -> int:
    return (a {operator} b) + 2
"""
    result = eval_uplc_value(
        source_code,
        a,
        b,
        config=DEFAULT_TEST_CONFIG.update(optimize_bool_only_ops=True),
    )
    expected = (a and b) if operator == "and" else (a or b)
    assert result == expected + 2
