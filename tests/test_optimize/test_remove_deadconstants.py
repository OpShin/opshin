import pytest

from opshin.compiler_config import OPT_O0_CONFIG, OPT_O1_CONFIG
from tests.utils import eval_uplc, Unit


@pytest.mark.parametrize(
    "conditional",
    [
        "if flag:\n        value = 1",
        "while flag:\n        value = 1\n        flag = False",
    ],
)
def test_dead_name_expression_preserves_unbound_name_error(conditional):
    source = f"""
def validator(flag: bool) -> None:
    {conditional}
    value
"""

    with pytest.raises(RuntimeError):
        eval_uplc(
            source,
            False,
            config=OPT_O1_CONFIG.update(wrap_output=True, unwrap_input=True),
        )


def test_dead_name_expression_is_removed_after_definite_assignment():
    source = """
def validator(_: None) -> None:
    value = 1
    value
"""

    unoptimized = OPT_O0_CONFIG.update(wrap_output=True, unwrap_input=True)
    optimized = OPT_O1_CONFIG.update(wrap_output=True, unwrap_input=True)
    assert eval_uplc(source, Unit(), config=optimized) == eval_uplc(
        source, Unit(), config=unoptimized
    )
