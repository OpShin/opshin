import unittest
from dataclasses import dataclass

from pycardano import PlutusData
from uplc import ast as uplc

from opshin import DEFAULT_CONFIG, builder
from tests.utils import eval_uplc_value, Unit, eval_uplc, eval_uplc_raw

DEFAULT_CONFIG_REMOVE_TRACE = DEFAULT_CONFIG.update(
    remove_trace=True, iterative_unfold_patterns=True
)


def test_remove_trace_remove_errors():
    source_code = """
from opshin.prelude import *

def validator(_: None) -> bytes:
    print("hello")
    assert 1 + 1 == 3, "math is ok"
    return b"\\x00\\x11"
"""
    res = eval_uplc_raw(source_code, Unit())
    assert res.logs == ["hello", "math is ok"]
    res = eval_uplc_raw(source_code, Unit(), config=DEFAULT_CONFIG_REMOVE_TRACE)
    assert res.logs == []


def test_remove_trace_correct():
    source_code = """
from opshin.prelude import *

def validator(_: None) -> bytes:
    print("hello")
    assert 1 + 1 == 2, "math is ok"
    return b"\\x00\\x11"
"""
    res = eval_uplc_raw(source_code, Unit())
    assert res.result.value == b"\x00\x11"
    res = eval_uplc_raw(source_code, Unit(), config=DEFAULT_CONFIG_REMOVE_TRACE)
    assert res.result.value == b"\x00\x11"
