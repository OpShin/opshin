import pytest
import uplc

from opshin import builder, compiler
from opshin.compiler_config import OPT_O0_CONFIG
from tests.utils import DEFAULT_TEST_CONFIG, eval_uplc_value

FALLTHROUGH_SOURCE = """
from typing import Union

def validator(value: Union[int, bytes]) -> int:
    if isinstance(value, int):
        value = value + 1
        result = value + value + value + value + value + value + value + value
    else:
        result = len(value)
    return result
"""


def test_rebinding_narrowed_value_preserves_fallthrough_and_assignment():
    assert eval_uplc_value(FALLTHROUGH_SOURCE, 4) == 40
    assert eval_uplc_value(FALLTHROUGH_SOURCE, b"abc") == 3


def test_rebinding_does_not_create_unbound_branch_state():
    source = """
from typing import Union

def validator(value: Union[int, bytes]) -> int:
    if isinstance(value, int):
        result = value + value + value + value + value + value + value + value + value
    else:
        result = len(value)
    return result
"""
    assert eval_uplc_value(source, 4) == 36
    assert eval_uplc_value(source, b"abc") == 3


def test_rebinding_narrowed_value_reduces_execution_cost():
    baseline_code = builder._compile(
        FALLTHROUGH_SOURCE,
        4,
        config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=False),
    )
    optimized_code = builder._compile(
        FALLTHROUGH_SOURCE,
        4,
        config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=True),
    )
    baseline = uplc.eval(baseline_code)
    optimized = uplc.eval(optimized_code)

    assert optimized.result == baseline.result
    assert optimized.cost.cpu < baseline.cost.cpu
    assert optimized.cost.memory < baseline.cost.memory


@pytest.mark.parametrize(
    ("source", "argument", "expected"),
    [
        (
            """
from typing import Union

def validator(value: Union[int, bytes]) -> int:
    if isinstance(value, bytes):
        return len(value) + len(value) + len(value) + len(value) + len(value) + len(value)
    return value
""",
            b"abc",
            18,
        ),
        (
            """
from typing import List, Union
from pycardano import Datum as Anything, PlutusData

def validator(value: Union[int, List[Anything]]) -> int:
    if isinstance(value, List):
        return len(value) + len(value) + len(value)
    return value
""",
            [1, 2, 3],
            9,
        ),
    ],
)
def test_rebinding_bytes_and_lists_reduces_execution_cost(source, argument, expected):
    baseline = uplc.eval(
        builder._compile(
            source,
            argument,
            config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=False),
        )
    )
    optimized = uplc.eval(
        builder._compile(
            source,
            argument,
            config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=True),
        )
    )

    assert optimized.result.value == expected
    assert optimized.cost.cpu < baseline.cost.cpu
    assert optimized.cost.memory < baseline.cost.memory


def test_rebinding_narrowed_value_in_loop_preserves_updates():
    source = """
from typing import Union

def validator(value: Union[int, bytes], count: int) -> int:
    total = 0
    while isinstance(value, int) and count > 0:
        total = total + value + value + value + value + value + value + value + value
        value = value + 1
        count = count - 1
    return total
"""
    assert eval_uplc_value(source, 2, 3) == 72
    assert eval_uplc_value(source, b"abc", 3) == 0


def test_rebinding_is_disabled_at_o0():
    source = """
from typing import Union

def validator(value: Union[int, bytes]) -> int:
    if isinstance(value, int):
        return value + value + value + value + value + value + value + value
    return len(value)
"""
    o0_config = OPT_O0_CONFIG.update(wrap_output=True, unwrap_input=True)
    implicit_o0 = builder._compile(
        source,
        4,
        config=o0_config,
    )
    explicit_o0 = builder._compile(
        source,
        4,
        config=o0_config.update(optimize_selective_narrowing=False),
    )
    assert uplc.flatten(implicit_o0) == uplc.flatten(explicit_o0)


def test_branch_reads_are_weighted_by_default_probability():
    source = """
from typing import Union

def validator(value: Union[int, bytes], early: bool) -> int:
    if isinstance(value, int):
        if early:
            return 0
        return value + value + value + value + value + value
    return 1
"""
    baseline = builder._compile(
        source,
        4,
        True,
        config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=False),
    )
    optimized = builder._compile(
        source,
        4,
        True,
        config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=True),
    )

    assert uplc.flatten(optimized) == uplc.flatten(baseline)


def test_branch_probability_hint_controls_expected_reads():
    source = """
from typing import Union

def validator(value: Union[int, bytes], early: bool) -> int:
    if isinstance(value, int):
        if early:  # opshin: branch-probability=0.0
            return 0
        return value + value + value + value + value + value
    return 1
"""
    tree = compiler.parse(source, filename="<unknown>")
    inner_if = tree.body[1].body[0].body[0]
    assert inner_if.branch_probability == 0.0

    baseline = uplc.eval(
        builder._compile(
            source,
            4,
            False,
            config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=False),
        )
    )
    optimized = uplc.eval(
        builder._compile(
            source,
            4,
            False,
            config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=True),
        )
    )

    assert optimized.result == baseline.result
    assert optimized.cost.cpu < baseline.cost.cpu


def test_iteration_hint_controls_expected_reads():
    source = """
from typing import List, Union

def validator(value: Union[int, bytes], items: List[int]) -> int:
    if isinstance(value, int):
        total = 0
        for item in items:  # opshin: iterations=6.0
            total += value
        return total
    return 0
"""
    tree = compiler.parse(source, filename="<unknown>")
    loop = tree.body[1].body[0].body[1]
    assert loop.iterations == 6.0

    baseline = uplc.eval(
        builder._compile(
            source,
            4,
            [1, 2, 3, 4, 5, 6],
            config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=False),
        )
    )
    optimized = uplc.eval(
        builder._compile(
            source,
            4,
            [1, 2, 3, 4, 5, 6],
            config=DEFAULT_TEST_CONFIG.update(optimize_selective_narrowing=True),
        )
    )

    assert optimized.result == baseline.result
    assert optimized.cost.cpu < baseline.cost.cpu


@pytest.mark.parametrize(
    "source",
    [
        "if True:  # opshin: branch-probability=1.1\n    pass\n",
        "for item in []:  # opshin: iterations=-1\n    pass\n",
        "while True:  # opshin: iterations=often\n    pass\n",
    ],
)
def test_invalid_cost_hints_are_rejected(source):
    with pytest.raises((AssertionError, ValueError)):
        compiler.parse(source, filename="<unknown>")
