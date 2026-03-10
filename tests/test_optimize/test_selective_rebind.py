from unittest.mock import patch

from opshin import builder
from opshin.util import NoOp
from tests.utils import eval_uplc_raw


def _compile_size(source_code: str) -> int:
    builder._static_compile.cache_clear()
    return len(builder._compile(source_code).dumps())


def _eval_with_optional_pass(source_code: str, *args, enabled: bool):
    builder._static_compile.cache_clear()
    if enabled:
        return eval_uplc_raw(source_code, *args)
    with patch("opshin.compiler.OptimizeSelectiveNarrowingRebind", NoOp):
        return eval_uplc_raw(source_code, *args)


def test_selective_rebind_repeated_reads():
    source_code = """
from typing import List, Union
from pycardano import Datum as Anything, PlutusData

def validator(v: Union[int, List[Anything]], n: int) -> int:
    if isinstance(v, List):
        x = len(v)
        y = len(v)
        return x + y + len(v)
    return 0
"""
    expected = 9
    without_eval = _eval_with_optional_pass(source_code, [1, 2, 3], 0, enabled=False)
    with_eval = _eval_with_optional_pass(source_code, [1, 2, 3], 0, enabled=True)
    with patch("opshin.compiler.OptimizeSelectiveNarrowingRebind", NoOp):
        without_pass = _compile_size(source_code)
    with_pass = _compile_size(source_code)
    assert without_eval.result.value == expected
    assert with_eval.result.value == expected
    assert with_eval.cost.cpu < without_eval.cost.cpu
    assert with_eval.cost.memory < without_eval.cost.memory
    assert with_pass >= without_pass


def test_selective_rebind_skips_simple_while_reassign():
    source_code = """
from typing import Union

def validator(a: Union[int, bytes]) -> int:
    while isinstance(a, int) and a > 0:
        a -= 1
    return 0
"""
    without_eval = _eval_with_optional_pass(source_code, 5, enabled=False)
    with_eval = _eval_with_optional_pass(source_code, 5, enabled=True)
    with patch("opshin.compiler.OptimizeSelectiveNarrowingRebind", NoOp):
        without_pass = _compile_size(source_code)
    with_pass = _compile_size(source_code)
    assert without_eval.result.value == 0
    assert with_eval.result.value == 0
    assert with_eval.cost.cpu == without_eval.cost.cpu
    assert with_eval.cost.memory == without_eval.cost.memory
    assert with_pass == without_pass


def test_selective_rebind_skips_atomic_repeated_reads():
    source_code = """
from typing import Union

def validator(v: Union[int, bytes]) -> int:
    if isinstance(v, int):
        return v + v
    return 0
"""
    without_eval = _eval_with_optional_pass(source_code, 5, enabled=False)
    with_eval = _eval_with_optional_pass(source_code, 5, enabled=True)
    with patch("opshin.compiler.OptimizeSelectiveNarrowingRebind", NoOp):
        without_pass = _compile_size(source_code)
    with_pass = _compile_size(source_code)
    assert without_eval.result.value == 10
    assert with_eval.result.value == 10
    assert with_eval.cost.cpu == without_eval.cost.cpu
    assert with_eval.cost.memory == without_eval.cost.memory
    assert with_pass == without_pass


def test_selective_rebind_skips_dict_repeated_reads():
    source_code = """
from typing import Dict, Union
from pycardano import Datum as Anything, PlutusData

def validator(v: Union[int, Dict[Anything, Anything]], n: int) -> int:
    if isinstance(v, Dict):
        return len(v) + len(v) + len(v)
    return 0
"""
    without_eval = _eval_with_optional_pass(
        source_code, {1: 2, 3: 4}, 0, enabled=False
    )
    with_eval = _eval_with_optional_pass(source_code, {1: 2, 3: 4}, 0, enabled=True)
    with patch("opshin.compiler.OptimizeSelectiveNarrowingRebind", NoOp):
        without_pass = _compile_size(source_code)
    with_pass = _compile_size(source_code)
    assert without_eval.result.value == 6
    assert with_eval.result.value == 6
    assert with_eval.cost.cpu == without_eval.cost.cpu
    assert with_eval.cost.memory == without_eval.cost.memory
    assert with_pass == without_pass
