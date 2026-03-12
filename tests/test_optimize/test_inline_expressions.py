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
