"""
Tests for the multi-pass optimizer pipeline.
These tests verify that the optimizer is run repeatedly until a fixed-point is reached,
enabling optimizations that depend on results from previous passes.
"""

from tests.utils import Unit, eval_uplc_raw

from opshin.compiler_config import DEFAULT_CONFIG

_OPT_CONFIG = DEFAULT_CONFIG.update(remove_dead_code=True)
_NO_OPT_CONFIG = DEFAULT_CONFIG.update(remove_dead_code=False)


def test_multipass_removes_var_only_used_in_dead_cond():
    """
    A variable that is only used inside a dead condition branch (if False)
    should be removed in two passes:
    Pass 1: OptimizeRemoveDeadConditions removes the dead if-block (and the var reference inside it)
    Pass 2: OptimizeRemoveDeadvars removes the now-unused variable assignment
    """
    source_code = """
def validator(_: None) -> int:
    y = 1
    if False:
        z = y
    return 0
"""
    target_code = """
def validator(_: None) -> int:
    return 0
"""
    source = eval_uplc_raw(source_code, Unit(), config=_OPT_CONFIG)
    target = eval_uplc_raw(target_code, Unit(), config=_NO_OPT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


def test_multipass_chain_of_dead_vars():
    """
    A chain of assignments where only the last is used in dead code
    should all be removed across multiple passes.
    Pass 1: dead condition removed, last var reference gone
    Pass 2: last var assignment becomes dead, removed
    Pass 3: intermediate var becomes dead, removed
    (etc.)
    """
    source_code = """
def validator(_: None) -> int:
    a = 1
    b = a + 1
    if False:
        c = b + 1
    return 0
"""
    target_code = """
def validator(_: None) -> int:
    return 0
"""
    source = eval_uplc_raw(source_code, Unit(), config=_OPT_CONFIG)
    target = eval_uplc_raw(target_code, Unit(), config=_NO_OPT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory
