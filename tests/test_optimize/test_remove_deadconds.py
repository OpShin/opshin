from opshin.compiler_config import DEFAULT_CONFIG
from tests.utils import eval_uplc_raw

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
