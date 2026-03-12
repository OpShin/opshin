"""
Tests for the multi-pass optimizer pipeline.
These tests verify that the optimizer is run repeatedly until a fixed-point is reached,
enabling optimizations that depend on results from previous passes.
"""

from tests.utils import DEFAULT_TEST_CONFIG, Unit, eval_uplc_raw

_OPT_CONFIG = DEFAULT_TEST_CONFIG
_NO_OPT_CONFIG = DEFAULT_TEST_CONFIG.update(remove_dead_code=False)


def test_multipass_removes_var_only_used_in_dead_cond():
    """
    A variable y that is only referenced inside a dead if-block requires two
    pipeline passes to fully remove:

    Pass 1: OptimizeRemoveDeadvars keeps y=1 because y appears referenced via z=y
            inside the dead block.  z itself appears alive because x=2*z and
            return z also reference it, and 2*z has a potential side-effect so
            OptimizeRemoveDeadvars cannot speculatively remove x=2*z.
            OptimizeRemoveDeadConditions then removes the entire if False block.

    Pass 2: OptimizeRemoveDeadvars now sees y has no references anywhere and
            removes y=1.

    Without the pipeline loop the test fails because y=1 is left in the compiled
    output, raising the execution cost above that of the clean target.
    """
    source_code = """
def validator(_: None) -> int:
    y = 1
    if False:
        z = y
        x = 2 * z
        return z
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
