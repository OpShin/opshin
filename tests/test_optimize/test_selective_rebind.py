import pytest

from opshin.optimize.optimize_selective_narrowing_rebind import (
    BYTESTRING_REBIND_READ_THRESHOLD,
    INTEGER_REBIND_READ_THRESHOLD,
    LIST_REBIND_READ_THRESHOLD,
    bytes_source,
    dict_source,
    eval_with_mode,
    int_source,
    list_source,
)

# If these tests fail after an UPLC version bump or optimizer change,
# rerun `uv run python scripts/recompute_selective_rebind_thresholds.py`
# and update the heuristic in
# `/Users/niels/git/opshin2/opshin/optimize/optimize_selective_narrowing_rebind.py`.

def _assert_auto_matches_cheapest(
    source_code: str,
    args: tuple,
    expected_value: int,
    forced_kind: str,
    expected_mode: str,
):
    noop_eval = eval_with_mode(source_code, *args, mode="noop")
    auto_eval = eval_with_mode(source_code, *args, mode="auto")
    forced_eval = eval_with_mode(
        source_code, *args, mode="forced", forced_kind=forced_kind
    )
    assert noop_eval.result.value == expected_value
    assert auto_eval.result.value == expected_value
    assert forced_eval.result.value == expected_value
    if expected_mode == "noop":
        assert noop_eval.cost.cpu <= forced_eval.cost.cpu
        assert noop_eval.cost.memory <= forced_eval.cost.memory
        assert auto_eval.cost.cpu == noop_eval.cost.cpu
        assert auto_eval.cost.memory == noop_eval.cost.memory
    elif expected_mode == "forced":
        assert forced_eval.cost.cpu <= noop_eval.cost.cpu
        assert forced_eval.cost.memory <= noop_eval.cost.memory
        assert auto_eval.cost.cpu == forced_eval.cost.cpu
        assert auto_eval.cost.memory == forced_eval.cost.memory
    else:
        raise AssertionError(f"Unknown expected mode {expected_mode}")


@pytest.mark.parametrize(
    ("source_code", "args", "expected_value", "forced_kind", "expected_mode"),
    [
        (
            list_source(LIST_REBIND_READ_THRESHOLD - 1),
            ([1, 2, 3], 0),
            3 * (LIST_REBIND_READ_THRESHOLD - 1),
            "list",
            "noop",
        ),
        (
            list_source(LIST_REBIND_READ_THRESHOLD),
            ([1, 2, 3], 0),
            3 * LIST_REBIND_READ_THRESHOLD,
            "list",
            "forced",
        ),
        (
            int_source(INTEGER_REBIND_READ_THRESHOLD - 2),
            (5,),
            5 * (INTEGER_REBIND_READ_THRESHOLD - 2),
            "int",
            "noop",
        ),
        (
            int_source(INTEGER_REBIND_READ_THRESHOLD),
            (5,),
            5 * INTEGER_REBIND_READ_THRESHOLD,
            "int",
            "forced",
        ),
        (
            bytes_source(BYTESTRING_REBIND_READ_THRESHOLD - 2),
            (b"abcde",),
            5 * (BYTESTRING_REBIND_READ_THRESHOLD - 2),
            "bytes",
            "noop",
        ),
        (
            bytes_source(BYTESTRING_REBIND_READ_THRESHOLD),
            (b"abcde",),
            5 * BYTESTRING_REBIND_READ_THRESHOLD,
            "bytes",
            "forced",
        ),
    ],
)
def test_selective_rebind_chooses_cheapest_mode(
    source_code: str,
    args: tuple,
    expected_value: int,
    forced_kind: str,
    expected_mode: str,
):
    _assert_auto_matches_cheapest(
        source_code, args, expected_value, forced_kind, expected_mode
    )


def test_selective_rebind_keeps_dict_disabled():
    _assert_auto_matches_cheapest(
        dict_source(4), ({1: 2, 3: 4}, 0), 8, "dict", "noop"
    )
