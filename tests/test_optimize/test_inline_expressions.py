import pytest

from opshin.compiler_config import DEFAULT_CONFIG
from tests.utils import eval_uplc, eval_uplc_raw, Unit

_DEFAULT_CONFIG = DEFAULT_CONFIG
_DEFAULT_INLINE_CONFIG = DEFAULT_CONFIG.update(remove_dead_code=True)


def test_inline_constant():
    """Inline a constant assignment: x = 5; y = x * 2 -> y = 5 * 2"""
    source_code = """
def validator(a: int) -> int:
    x = 5
    return x + a
"""
    target_code = """
def validator(a: int) -> int:
    return 5 + a
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_inline_name():
    """Inline a name assignment: x = a; y = x * 2 -> y = a * 2"""
    source_code = """
def validator(a: int) -> int:
    x = a
    return x * 2
"""
    target_code = """
def validator(a: int) -> int:
    return a * 2
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_inline_chain():
    """Inline a chain: a = 5; b = a; c = b -> c = 5"""
    source_code = """
def validator(_: None) -> int:
    a = 5
    b = a
    c = b
    return c
"""
    target_code = """
def validator(_: None) -> int:
    return 5
"""
    source = eval_uplc_raw(source_code, Unit(), config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, Unit(), config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_inline_constant_multiple_reads():
    """Inline a constant even when read multiple times"""
    source_code = """
def validator(_: None) -> int:
    x = 10
    return x + x
"""
    target_code = """
def validator(_: None) -> int:
    return 10 + 10
"""
    source = eval_uplc_raw(source_code, Unit(), config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, Unit(), config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_no_inline_multiple_assign():
    """Do not inline a variable that is assigned multiple times"""
    source_code = """
def validator(_: None) -> int:
    x = 5
    x = 10
    return x
"""
    source = eval_uplc(source_code, Unit(), config=_DEFAULT_INLINE_CONFIG)
    # should return 10, not 5
    assert source.value == 10


def test_inline_preserves_semantics():
    """Inlining should preserve computation semantics"""
    source_code = """
def validator(a: int) -> int:
    x = a
    y = x + 1
    z = y + 1
    return z
"""
    source = eval_uplc(source_code, 3, config=_DEFAULT_INLINE_CONFIG)
    assert source.value == 5


def test_inline_in_function():
    """Inlining should work inside function bodies"""
    source_code = """
def validator(a: int) -> int:
    x = 1
    y = x + a
    return y
"""
    target_code = """
def validator(a: int) -> int:
    return 1 + a
"""
    source = eval_uplc_raw(source_code, 7, config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, 7, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_no_inline_unsafe_in_branch():
    """Do not inline an unsafe expression when only used inside a branch.

    x = 1 // 0 always crashes. If incorrectly inlined into the False branch,
    the crash would be removed by dead condition elimination, changing semantics.
    """
    source_code = """
def validator(_: None) -> int:
    x = 1 // 0
    if False:
        return x
    return 0
"""
    with pytest.raises(RuntimeError):
        eval_uplc(source_code, Unit(), config=_DEFAULT_INLINE_CONFIG)


def test_no_inline_multiple_reads_non_simple():
    """Do not inline a non-simple expression used multiple times"""
    source_code = """
def validator(a: int) -> int:
    x = a + 1
    return x + x
"""
    source = eval_uplc(source_code, 4, config=_DEFAULT_INLINE_CONFIG)
    assert source.value == 10


def test_inline_guaranteed_execution():
    """Inline a non-safe expression when the use is guaranteed to execute.

    a + 1 is not safe (BinOp), but since `return x` is at the top level
    (not inside a branch), every code path from the assignment reaches
    the use, so inlining is safe.
    """
    source_code = """
def validator(a: int) -> int:
    x = a + 1
    return x
"""
    target_code = """
def validator(a: int) -> int:
    return a + 1
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_inline_inside_if_branch():
    """Inline within an if branch without propagating beyond the branch boundary."""
    source_code = """
def validator(a: int) -> int:
    if a > 0:
        x = 5
        return x + a
    return 0
"""
    target_code = """
def validator(a: int) -> int:
    if a > 0:
        return 5 + a
    return 0
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_inline_inside_else_branch():
    """Inline within an else branch without requiring whole-function propagation."""
    source_code = """
def validator(a: int) -> int:
    if a > 0:
        return a
    else:
        x = 5
        return x + 1
"""
    target_code = """
def validator(a: int) -> int:
    if a > 0:
        return a
    else:
        return 5 + 1
"""
    source = eval_uplc_raw(source_code, -1, config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, -1, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_no_inline_across_if_else_merge():
    """Do not propagate a branch-local assignment across the if/else merge."""
    source_code = """
def validator(flag: int) -> int:
    x = 0
    if flag > 0:
        x = 1
    else:
        x = 2
    return x
"""
    source_true = eval_uplc(source_code, 1, config=_DEFAULT_INLINE_CONFIG)
    source_false = eval_uplc(source_code, 0, config=_DEFAULT_INLINE_CONFIG)

    assert source_true.value == 1
    assert source_false.value == 2


def test_no_inline_loop_carried_state_inside_while_body():
    """Do not inline assignments that update loop-carried state from outside the body."""
    source_code = """
def validator(n: int) -> int:
    total = 0
    i = 0
    while i < n:
        total = total + i
        i = i + 1
    return total
"""
    source_zero = eval_uplc(source_code, 0, config=_DEFAULT_INLINE_CONFIG)
    source_three = eval_uplc(source_code, 3, config=_DEFAULT_INLINE_CONFIG)

    assert source_zero.value == 0
    assert source_three.value == 3


def test_no_inline_loop_carried_state_inside_for_body():
    """Do not inline loop-carried state updates inside a for body either."""
    source_code = """
def validator(n: int) -> int:
    total = 0
    for i in range(n):
        total = total + i
    return total
"""
    source_zero = eval_uplc(source_code, 0, config=_DEFAULT_INLINE_CONFIG)
    source_four = eval_uplc(source_code, 4, config=_DEFAULT_INLINE_CONFIG)

    assert source_zero.value == 0
    assert source_four.value == 6


def test_inline_not_blocked_by_nested_function_argument_shadowing():
    """Nested function arguments should not prevent inlining in the outer scope."""
    source_code = """
def validator(a: int) -> int:
    x = a
    def inner(x: int) -> int:
        return x + 1
    return inner(a) + x
"""
    target_code = """
def validator(a: int) -> int:
    def inner(x: int) -> int:
        return x + 1
    return inner(a) + a
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_inline_not_blocked_by_nested_function_local_shadowing():
    """Nested local assignments should not poison outer-scope inlining."""
    source_code = """
def validator(a: int) -> int:
    x = a
    def inner(y: int) -> int:
        x = y + 1
        return x
    return inner(a) + x
"""
    target_code = """
def validator(a: int) -> int:
    def inner(y: int) -> int:
        x = y + 1
        return x
    return inner(a) + a
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_INLINE_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory
