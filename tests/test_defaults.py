import pytest

from opshin import builder
from opshin.compiler_config import OPT_O3_CONFIG

from .utils import Unit, eval_uplc_raw, eval_uplc_value


def test_positional_default_argument():
    source_code = """
def add(x: int, y: int = 2) -> int:
    return x + y

def validator(x: int) -> int:
    return add(x)
"""

    assert eval_uplc_value(source_code, 3) == 5


def test_positional_argument_overrides_default():
    source_code = """
def add(x: int, y: int = 2) -> int:
    return x + y

def validator(x: int) -> int:
    return add(x, 4)
"""

    assert eval_uplc_value(source_code, 3) == 7


def test_multiple_defaults_and_keywords():
    source_code = """
def number(x: int, y: int = 2, z: int = 3) -> int:
    return 100 * x + 10 * y + z

def validator(x: int) -> int:
    return number(z=9, x=x)
"""

    assert eval_uplc_value(source_code, 1) == 129


def test_default_argument_in_forward_call():
    source_code = """
def first(x: int) -> int:
    return second(x)

def second(x: int, y: int = 4) -> int:
    return x * y

def validator(x: int) -> int:
    return first(x)
"""

    assert eval_uplc_value(source_code, 3) == 12


def test_default_argument_in_recursive_call():
    source_code = """
def sum_down(x: int, step: int = 1) -> int:
    if x <= 0:
        return 0
    return x + sum_down(x - step)

def validator(x: int) -> int:
    return sum_down(x)
"""

    assert eval_uplc_value(source_code, 3) == 6


def test_default_argument_through_function_alias():
    source_code = """
def add(x: int, y: int = 2) -> int:
    return x + y

def validator(x: int) -> int:
    alias = add
    return alias(x)
"""

    assert eval_uplc_value(source_code, 3) == 5


def test_method_default_argument():
    source_code = """
from opshin.prelude import *

@dataclass
class A(PlutusData):
    x: int

    def add(self, y: int = 2) -> int:
        return self.x + y

def validator(x: int) -> int:
    return A(x).add()
"""

    assert eval_uplc_value(source_code, 3) == 5


def test_method_default_can_be_overridden_by_keyword():
    source_code = """
from opshin.prelude import *

@dataclass
class A(PlutusData):
    x: int

    def add(self, y: int = 2) -> int:
        return self.x + y

def validator(x: int) -> int:
    return A(x).add(y=4)
"""

    assert eval_uplc_value(source_code, 3) == 7


def test_defaults_with_mixed_types():
    source_code = """
from typing import List

def mixed(
    prefix: bytes = b"op",
    values: List[int] = [1, 2, 3],
    enabled: bool = True,
) -> int:
    if enabled and len(values) == 3:
        return len(prefix) + values[0]
    return 0

def validator() -> int:
    return mixed()
"""

    assert eval_uplc_value(source_code, Unit()) == 3


def test_defaults_with_mixed_types_can_be_overridden():
    source_code = """
from typing import List

def mixed(
    prefix: bytes = b"op",
    values: List[int] = [1, 2, 3],
    enabled: bool = True,
) -> int:
    if enabled:
        return len(prefix) + values[0]
    return 0

def validator() -> int:
    return mixed(values=[9], prefix=b"x")
"""

    assert eval_uplc_value(source_code, Unit()) == 10


def test_default_expression_is_evaluated_at_definition_time():
    source_code = """
def failing_default() -> int:
    assert False, "default evaluated"
    return 0

def validator() -> int:
    def unused(x: int = failing_default()) -> int:
        return x
    return 1
"""

    result = eval_uplc_raw(source_code, Unit())
    assert isinstance(result.result, RuntimeError)
    assert result.logs == ["default evaluated"]


def test_default_expression_is_evaluated_only_once():
    source_code = """
def make_default() -> int:
    print("default evaluated")
    return 2

def validator() -> int:
    def add(x: int = make_default()) -> int:
        return x
    return add() + add()
"""

    result = eval_uplc_raw(source_code, Unit())
    assert result.result.value == 4
    assert result.logs == ["default evaluated"]


def test_default_expression_uses_definition_scope():
    source_code = """
def validator(x: int) -> int:
    captured = x + 1
    def get_default(value: int = captured) -> int:
        return value
    captured = 5
    return get_default()
"""

    assert eval_uplc_value(source_code, 3) == 4


def test_default_argument_with_union_expansion():
    source_code = """
from typing import Union

def value(x: Union[int, bytes] = 1) -> int:
    if isinstance(x, int):
        return x
    return len(x)

def validator() -> int:
    return value()
"""

    config = OPT_O3_CONFIG.update(
        expand_union_types=True, wrap_output=True, unwrap_input=True
    )
    assert eval_uplc_value(source_code, Unit(), config=config) == 1


def test_hidden_default_binding_does_not_overwrite_user_variable():
    source_code = """
__opshin_default_0 = 40

def add(x: int = 2) -> int:
    return x

def validator() -> int:
    return __opshin_default_0 + add()
"""

    assert eval_uplc_value(source_code, Unit()) == 42


def test_hidden_default_binding_does_not_overwrite_deliberately_named_parameter():
    source_code = """
def validator(__opshin_default_0: int) -> int:
    def add(x: int = 2) -> int:
        return x
    return __opshin_default_0 + add()
"""

    assert eval_uplc_value(source_code, 40) == 42


def test_hidden_default_binding_does_not_collide_with_function_declaration():
    source_code = """
def value(x: int = 2) -> int:
    return x

def __opshin_default_0() -> int:
    return 99

def validator() -> int:
    return value()
"""

    assert eval_uplc_value(source_code, Unit()) == 2


def test_default_value_must_match_parameter_type():
    source_code = """
def add(x: int, y: int = b"wrong") -> int:
    return x + y

def validator(x: int) -> int:
    return add(x)
"""

    with pytest.raises(Exception, match="Default value"):
        builder._compile(source_code)


def test_missing_required_argument_is_rejected():
    source_code = """
def add(x: int, y: int = 2) -> int:
    return x + y

def validator() -> int:
    return add()
"""

    with pytest.raises(Exception, match="argument"):
        builder._compile(source_code)
