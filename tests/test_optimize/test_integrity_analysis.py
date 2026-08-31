import uplc
import logging
from frozenlist2 import frozenlist
from uplc.ast import PlutusConstr, PlutusList

from opshin import builder
from opshin.typed_ast import TypedAST
from tests.utils import DEFAULT_TEST_CONFIG

MALFORMED_BYTES = PlutusList(frozenlist([]))


def test_integrity_is_part_of_typed_ast_data_model():
    assert TypedAST.__annotations__["integrity_checked"] is bool


def _evaluate(source, *args, selective_narrowing):
    return uplc.eval(
        builder._compile(
            source,
            *args,
            config=DEFAULT_TEST_CONFIG.update(
                optimize_selective_narrowing=selective_narrowing,
                remove_trace=False,
            ),
        )
    )


def test_integrity_unchecked_value_is_not_eagerly_narrowed_in_short_circuit():
    source = """
from typing import Union

def validator(value: Union[int, bytes], early: bool) -> int:
    if isinstance(value, int):
        return 1
    else:
        if early or len(value) + len(value) + len(value) + len(value) + len(value) + len(value) + len(value) + len(value) + len(value) + len(value) + len(value) + len(value) > 0:
            return 0
        return 2
"""

    baseline = _evaluate(source, MALFORMED_BYTES, True, selective_narrowing=False)
    optimized = _evaluate(source, MALFORMED_BYTES, True, selective_narrowing=True)

    assert baseline.result.value == 0
    assert optimized.result == baseline.result


def test_integrity_unchecked_atomic_decode_does_not_warn(caplog):
    source = """
def validator(value: int) -> int:
    return value + 1
"""

    with caplog.at_level(logging.WARNING, logger="opshin"):
        builder._compile(
            source,
            b"abc",
            config=DEFAULT_TEST_CONFIG.update(
                optimize_selective_narrowing=False,
                optimize_remove_checked_integrity_checks=False,
            ),
        )

    assert "Integrity-unchecked value" not in caplog.text


def test_integrity_unchecked_negative_union_narrowing_warns(caplog):
    source = """
from typing import Union

def validator(value: Union[int, bytes]) -> int:
    if isinstance(value, int):
        return value
    else:
        return len(value)
"""

    with caplog.at_level(logging.WARNING, logger="opshin"):
        builder._compile(source, config=DEFAULT_TEST_CONFIG)

    assert "value 'value' is treated as 'bytes'" in caplog.text
    assert "malformed data may enter this branch" in caplog.text


def test_integrity_checked_negative_union_narrowing_does_not_warn(caplog):
    source = """
from typing import Union
from opshin.std.integrity import check_integrity

def validator(value: Union[int, bytes]) -> int:
    check_integrity(value)
    if isinstance(value, int):
        return value
    else:
        return len(value)
"""

    with caplog.at_level(logging.WARNING, logger="opshin"):
        builder._compile(source, config=DEFAULT_TEST_CONFIG)

    assert "is treated as" not in caplog.text


def test_integrity_unchecked_equality_emits_security_warning(caplog):
    source = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData

@dataclass
class Datum(PlutusData):
    CONSTR_ID = 0
    value: int

def validator(left: Datum, right: Datum) -> bool:
    return left == right
"""

    with caplog.at_level(logging.WARNING, logger="opshin"):
        builder._compile(source, config=DEFAULT_TEST_CONFIG)

    assert "Integrity-unchecked value 'left' is used" in caplog.text
    assert "Integrity-unchecked value 'right' is used" in caplog.text


def test_integrity_unchecked_function_result_is_not_eagerly_narrowed():
    source = """
from typing import Union

def identity(value: Union[int, bytes]) -> Union[int, bytes]:
    return value

def validator(value: Union[int, bytes], early: bool) -> int:
    result = identity(value)
    if isinstance(result, int):
        return 1
    else:
        if early or len(result) + len(result) + len(result) + len(result) + len(result) + len(result) + len(result) + len(result) + len(result) + len(result) + len(result) + len(result) > 0:
            return 0
        return 2
"""

    baseline = _evaluate(source, MALFORMED_BYTES, True, selective_narrowing=False)
    optimized = _evaluate(source, MALFORMED_BYTES, True, selective_narrowing=True)

    assert baseline.result.value == 0
    assert optimized.result == baseline.result


def test_integrity_check_makes_negative_narrowing_safe_and_profitable():
    source = """
from typing import Union
from opshin.std.integrity import check_integrity

def validator(value: Union[int, bytes]) -> int:
    check_integrity(value)
    if isinstance(value, int):
        return value
    else:
        return len(value) + len(value) + len(value) + len(value) + len(value) + len(value)
"""

    baseline = _evaluate(source, b"abc", selective_narrowing=False)
    optimized = _evaluate(source, b"abc", selective_narrowing=True)

    assert optimized.result == baseline.result
    assert optimized.cost.cpu < baseline.cost.cpu
    assert optimized.cost.memory < baseline.cost.memory


def test_successful_atomic_decode_makes_function_result_integrity_checked():
    checked = """
from typing import Union
from opshin.std.integrity import check_integrity

def clean_by_use(value: Union[int, bytes]) -> Union[int, bytes]:
    if isinstance(value, int):
        return value + 0
    else:
        initial_length = len(value)
        return value

def validator(value: Union[int, bytes]) -> None:
    result = clean_by_use(value)
    check_integrity(result)
"""
    unchecked = checked.replace("    check_integrity(result)\n", "    pass\n")

    checked_program = builder._compile(checked, b"abc", config=DEFAULT_TEST_CONFIG)
    unchecked_program = builder._compile(unchecked, b"abc", config=DEFAULT_TEST_CONFIG)

    assert uplc.flatten(checked_program) == uplc.flatten(unchecked_program)


def test_redundant_integrity_check_of_constructed_value_is_removed():
    checked = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    value: int

def validator(value: int) -> None:
    wrapped = A(value)
    check_integrity(wrapped)
"""
    unchecked = checked.replace("    check_integrity(wrapped)\n", "    pass\n")

    checked_program = builder._compile(checked, 4, config=DEFAULT_TEST_CONFIG)
    unchecked_program = builder._compile(unchecked, 4, config=DEFAULT_TEST_CONFIG)

    assert uplc.flatten(checked_program) == uplc.flatten(unchecked_program)


def test_integrity_check_of_integrity_unchecked_parameter_is_retained():
    source = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    value: int

def validator(value: A) -> None:
    check_integrity(value)
"""

    result = _evaluate(source, MALFORMED_BYTES, selective_narrowing=True)

    assert isinstance(result.result, Exception)


def test_function_summary_propagates_checked_result_integrity():
    checked_twice = """
from typing import Union
from opshin.std.integrity import check_integrity

def clean(value: Union[int, bytes]) -> Union[int, bytes]:
    check_integrity(value)
    return value

def validator(value: Union[int, bytes]) -> None:
    result = clean(value)
    check_integrity(result)
"""
    checked_once = checked_twice.replace("    check_integrity(result)\n", "    pass\n")

    twice_program = builder._compile(checked_twice, b"abc", config=DEFAULT_TEST_CONFIG)
    once_program = builder._compile(checked_once, b"abc", config=DEFAULT_TEST_CONFIG)

    assert uplc.flatten(twice_program) == uplc.flatten(once_program)


def test_attribute_of_integrity_unchecked_value_remains_integrity_unchecked():
    source = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass
class Inner(PlutusData):
    CONSTR_ID = 1
    value: int

@dataclass
class Outer(PlutusData):
    CONSTR_ID = 0
    inner: Inner

def validator(value: Outer) -> None:
    check_integrity(value.inner)
"""
    malformed_inner = PlutusConstr(0, frozenlist([MALFORMED_BYTES]))

    result = _evaluate(source, malformed_inner, selective_narrowing=True)

    assert isinstance(result.result, Exception)


def test_branch_join_drops_integrity():
    source = """
from typing import Union
from opshin.std.integrity import check_integrity

def validator(
    value: Union[int, bytes], clean_value: bool
) -> None:
    if clean_value:
        check_integrity(value)
    check_integrity(value)
"""

    result = _evaluate(source, MALFORMED_BYTES, False, selective_narrowing=True)

    assert isinstance(result.result, Exception)


def test_reassignment_drops_integrity():
    source = """
from typing import Union
from opshin.std.integrity import check_integrity

def validator(first: Union[int, bytes], second: Union[int, bytes]) -> None:
    check_integrity(first)
    first = second
    check_integrity(first)
"""

    result = _evaluate(source, 1, MALFORMED_BYTES, selective_narrowing=True)

    assert isinstance(result.result, Exception)


def test_builtin_result_is_integrity_checked_by_function_summary():
    checked = """
from typing import Union
from hashlib import sha256
from opshin.std.integrity import check_integrity

def hashed(value: bytes) -> Union[int, bytes]:
    return sha256(value).digest()

def validator(value: bytes) -> None:
    result = hashed(value)
    check_integrity(result)
"""
    unchecked = checked.replace("    check_integrity(result)\n", "    pass\n")

    checked_program = builder._compile(checked, b"abc", config=DEFAULT_TEST_CONFIG)
    unchecked_program = builder._compile(unchecked, b"abc", config=DEFAULT_TEST_CONFIG)

    assert uplc.flatten(checked_program) == uplc.flatten(unchecked_program)


def test_functions_with_ten_parameters_have_no_integrity_summary():
    checked_twice = """
from typing import Union
from opshin.std.integrity import check_integrity

def clean(
    value: Union[int, bytes], a: int, b: int, c: int, d: int,
    e: int, f: int, g: int, h: int, i: int
) -> Union[int, bytes]:
    check_integrity(value)
    return value

def validator(value: Union[int, bytes]) -> None:
    result = clean(value, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    check_integrity(result)
"""
    checked_once = checked_twice.replace("    check_integrity(result)\n", "    pass\n")

    twice_program = builder._compile(checked_twice, b"abc", config=DEFAULT_TEST_CONFIG)
    once_program = builder._compile(checked_once, b"abc", config=DEFAULT_TEST_CONFIG)

    assert uplc.flatten(twice_program) != uplc.flatten(once_program)


def test_script_context_structure_is_integrity_checked():
    checked = """
from opshin.ledger.api_v3 import *
from opshin.std.integrity import check_integrity

def validator(context: ScriptContext) -> None:
    check_integrity(context.transaction)
"""
    unchecked = checked.replace(
        "    check_integrity(context.transaction)\n", "    pass\n"
    )

    checked_program = builder._compile(checked, config=DEFAULT_TEST_CONFIG)
    unchecked_program = builder._compile(unchecked, config=DEFAULT_TEST_CONFIG)

    assert uplc.flatten(checked_program) == uplc.flatten(unchecked_program)


def test_script_context_redeemer_payload_is_integrity_unchecked(caplog):
    source = """
from opshin.ledger.api_v3 import *

def validator(context: ScriptContext) -> bool:
    return context.redeemer == context.redeemer
"""
    config = DEFAULT_TEST_CONFIG.update(allow_isinstance_anything=True)

    with caplog.at_level(logging.WARNING, logger="opshin"):
        builder._compile(source, config=config)

    assert "Integrity-unchecked value 'context.redeemer' is used" in caplog.text
