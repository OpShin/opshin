import pytest

from opshin.compiler_config import DEFAULT_CONFIG
from tests.utils import Unit, eval_uplc, eval_uplc_raw

_DEFAULT_CONFIG = DEFAULT_CONFIG
_DEFAULT_UNFOLD_CONFIG = DEFAULT_CONFIG.update(remove_dead_code=True)


def test_remove_simple_dead_conds():
    source_code = """

def validator(x: int) -> int:
    return 1 if True else 0
"""
    target_code = """
def validator(x: int) -> int:
    return 1
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory


def test_remove_dead_conds_if():
    source_code = """
def validator(x: int) -> int:
    if True:
        return 1
    else:
        return 0
"""
    target_code = """
def validator(x: int) -> int:
    return 1
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory


def test_remove_dead_conds_while():
    source_code = """
def validator(x: int) -> int:
    i = 0
    while False:
        i = i + 1
    return i
"""
    target_code = """
def validator(x: int) -> int:
    i = 0
    return i
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory


def test_remove_dead_conds_preserve_if_local_scoping():
    source_code = """
def validator(_: None) -> int:
    if False:
        a = 10
    return a
"""
    with pytest.raises(RuntimeError):
        eval_uplc(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)


def test_remove_dead_conds_preserve_while_local_scoping():
    source_code = """
def validator(_: None) -> int:
    while False:
        a = 10
    return a
"""
    with pytest.raises(RuntimeError):
        eval_uplc(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)


def test_remove_dead_conds_preserve_short_circuit_failures():
    source_code = """
def validator(_: None) -> int:
    if (1 // 0 == 0) or True:
        return 1
    return 0
"""
    with pytest.raises(RuntimeError):
        eval_uplc(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)


def test_remove_dead_conds_short_circuit_true_or():
    source_code = """
def validator(_: None) -> int:
    if True or (1 // 0 == 0):
        return 1
    return 0
"""
    target_code = """
def validator(_: None) -> int:
    return 1
"""
    source = eval_uplc_raw(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, Unit(), config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory


def test_remove_dead_conds_short_circuit_false_and():
    source_code = """
def validator(_: None) -> int:
    if False and (1 // 0 == 0):
        return 1
    return 0
"""
    target_code = """
def validator(_: None) -> int:
    return 0
"""
    source = eval_uplc_raw(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, Unit(), config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory
