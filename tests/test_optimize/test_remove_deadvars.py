import pytest

from opshin.compiler_config import DEFAULT_CONFIG
from opshin.prelude import Token
from tests.utils import Unit, eval_uplc, eval_uplc_raw

_DEFAULT_CONFIG = DEFAULT_CONFIG
_DEFAULT_UNFOLD_CONFIG = DEFAULT_CONFIG.update(remove_dead_code=True)

# A valid Token with a 28-byte policy_id
VALID_TOKEN = Token(b"policy1234567890123456789012", b"mytoken")


def test_dead_var_unsafe_expr_side_effect_preserved():
    """Dead Expr with unsafe expression: crashes with invalid input, succeeds with valid input."""
    source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    x.policy_id
    return True
"""
    # Unit() is not a Token, so accessing policy_id must still fail after optimization
    with pytest.raises(RuntimeError):
        eval_uplc(source_code, Unit(), config=_DEFAULT_UNFOLD_CONFIG)

    # A real Token succeeds
    ret = eval_uplc(source_code, VALID_TOKEN, config=_DEFAULT_UNFOLD_CONFIG)
    assert ret.value is True


def test_dead_expr_name_removed():
    """Standalone Name expression (Expr(Name)) is removed since it is side-effect-free."""
    source_code = """
def validator(x: int) -> int:
    x
    return x + 1
"""
    target_code = """
def validator(x: int) -> int:
    return x + 1
"""
    source = eval_uplc_raw(source_code, 4, config=_DEFAULT_UNFOLD_CONFIG)
    target = eval_uplc_raw(target_code, 4, config=_DEFAULT_CONFIG)

    assert source.result == target.result
    assert source.cost.cpu <= target.cost.cpu
    assert source.cost.memory <= target.cost.memory


@pytest.mark.parametrize(
    "source_code",
    [
        pytest.param(
            """
def validator(flag: int) -> None:
    if flag > 0:
        authorized = 1
    authorized
""",
            id="if",
        ),
        pytest.param(
            """
def validator(flag: int) -> None:
    while flag > 0:
        authorized = 1
        flag = 0
    authorized
""",
            id="while",
        ),
        pytest.param(
            """
def validator(flag: int) -> None:
    for i in range(flag):
        authorized = 1
    authorized
""",
            id="for",
        ),
    ],
)
def test_dead_expr_conditional_name_load_preserves_unbound_error(source_code):
    """Path-local assignments must not make later name loads unconditionally safe."""
    with pytest.raises(RuntimeError):
        eval_uplc(
            source_code,
            0,
            config=_DEFAULT_CONFIG.update(remove_dead_code=False),
        )

    with pytest.raises(RuntimeError):
        eval_uplc(source_code, 0, config=_DEFAULT_UNFOLD_CONFIG)

    eval_uplc(source_code, 1, config=_DEFAULT_UNFOLD_CONFIG)
