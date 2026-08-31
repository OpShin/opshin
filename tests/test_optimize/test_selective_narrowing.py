import pytest
import uplc

from opshin import builder
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
