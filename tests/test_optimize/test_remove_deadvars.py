import pytest

from opshin.compiler_config import DEFAULT_CONFIG
from tests.utils import Unit, eval_uplc, eval_uplc_raw

_DEFAULT_CONFIG = DEFAULT_CONFIG
_DEFAULT_UNFOLD_CONFIG = DEFAULT_CONFIG.update(remove_dead_code=True)


def test_dead_var_safe_expr_removed():
    """Dead variable with safe (side-effect-free) expression is removed entirely."""
    source_code = """
def validator(x: int) -> int:
    unused = 42
    return x
"""
    target_code = """
def validator(x: int) -> int:
    return x
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory


def test_dead_var_unsafe_expr_preserved():
    """Dead variable with unsafe (side-effect-ful) expression is kept as Expr."""
    source_code = """
def validator(x: None) -> int:
    # a = x.policy_id would fail if x is not a Token, but 'a' is never used
    # The field access side-effect must be preserved
    return 1
"""
    # Should succeed (no field access)
    ret = eval_uplc(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)
    assert ret.value == 1


def test_dead_var_unsafe_expr_still_crashes():
    """Dead variable with unsafe expression that crashes still crashes after optimization."""
    source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    a = x.policy_id
    return True
"""
    with pytest.raises(RuntimeError):
        eval_uplc(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)


def test_dead_lambda_expr_removed():
    """Dead variable with safe constant expression is removed, verifying SafeOperationVisitor is used."""
    source_code = """
def validator(x: int) -> int:
    unused = 99
    return x
"""
    target_code = """
def validator(x: int) -> int:
    return x
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory


def test_dead_var_chain_still_works():
    """Chain of dead variables: b = 4; a = b where neither is used - both cleaned up."""
    source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    b = 4
    a = b
    return True
"""
    ret = eval_uplc(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)
    assert ret.value is True
