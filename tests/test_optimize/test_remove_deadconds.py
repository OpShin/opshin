import pytest
from opshin.compiler_config import DEFAULT_CONFIG, OPT_O1_CONFIG
from tests.utils import eval_uplc_raw, DEFAULT_TEST_CONFIG

_DEFAULT_CONFIG = DEFAULT_CONFIG
_DEFAULT_UNFOLD_CONFIG = OPT_O1_CONFIG


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


def test_remove_dead_conds_ifexp_false():
    source_code = """
def validator(x: int) -> int:
    return 1 if False else 0
"""
    target_code = """
def validator(x: int) -> int:
    return 0
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


def test_remove_dead_conds_if_false():
    source_code = """
def validator(x: int) -> int:
    if False:
        return 0
    else:
        return 1
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


def test_remove_dead_conds_while_true_raises():
    source_code = """
def validator(x: int) -> int:
    i = 0
    while True:
        i = i + 1
    return i
"""
    with pytest.raises(Exception):
        eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)


def test_remove_dead_conds_unary_not_false():
    source_code = """
def validator(x: int) -> int:
    return 1 if not False else 0
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


def test_remove_dead_conds_unary_not_true():
    source_code = """
def validator(x: int) -> int:
    return 1 if not True else 0
"""
    target_code = """
def validator(x: int) -> int:
    return 0
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory


def test_remove_dead_conds_boolop_and_false():
    source_code = """
def validator(x: int) -> int:
    if False and x > 0:
        return 1
    else:
        return 0
"""
    target_code = """
def validator(x: int) -> int:
    return 0
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu >= target.cost.cpu
    assert source.cost.memory >= target.cost.memory


def test_remove_dead_conds_boolop_or_true():
    source_code = """
def validator(x: int) -> int:
    if True or x > 0:
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


def test_remove_dead_conds_nested_if():
    source_code = """
def validator(x: int) -> int:
    if True:
        if False:
            return 0
        else:
            return 1
    else:
        return 2
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

