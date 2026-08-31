import ast

import pytest

from opshin import builder
from opshin.compiler_config import OPT_O3_CONFIG
from opshin.rewrite.rewrite_adjacent_inline import RewriteAdjacentInline
from tests.utils import Unit, eval_uplc, eval_uplc_value

INLINE_CONFIG = OPT_O3_CONFIG.update(wrap_output=True, unwrap_input=True)
NO_INLINE_CONFIG = INLINE_CONFIG.update(adjacent_inline=False)


def script_size(source_code: str, *args, config=INLINE_CONFIG) -> int:
    builder._static_compile.cache_clear()
    return len(builder._build(builder._compile(source_code, *args, config=config)))


def rewrite(source_code: str) -> str:
    rewritten = RewriteAdjacentInline().visit(ast.parse(source_code))
    return ast.dump(rewritten, include_attributes=False)


def test_inline_adjacent_return():
    source_code = """
def validator(a: int) -> int:
    x = a + 1
    return x
"""
    target_code = """
def validator(a: int) -> int:
    return a + 1
"""

    assert script_size(source_code, 4) == script_size(target_code, 4)


def test_inline_chain_to_fixed_point():
    source_code = """
def validator(a: int) -> int:
    x = a + 1
    y = x
    return y
"""
    target_code = """
def validator(a: int) -> int:
    return a + 1
"""

    assert script_size(source_code, 4) == script_size(target_code, 4)


def test_inline_chain_in_single_rewrite():
    source_code = """
def validator(a: int) -> int:
    x = a + 1
    y = x
    z = y
    return z
"""
    target_code = """
def validator(a: int) -> int:
    return a + 1
"""

    assert rewrite(source_code) == rewrite(target_code)


def test_inline_non_adjacent_straight_line_expression():
    source_code = """
def validator(a: int) -> int:
    x = a + 1
    z = 1
    return x + z
"""
    target_code = """
def validator(a: int) -> int:
    z = 1
    return a + 1 + z
"""

    assert script_size(source_code, 4) == script_size(target_code, 4)


def test_inline_inside_branch():
    source_code = """
def validator(a: int) -> int:
    if a > 0:
        x = a + 1
        return x
    return 0
"""
    target_code = """
def validator(a: int) -> int:
    if a > 0:
        return a + 1
    return 0
"""

    assert script_size(source_code, 4) == script_size(target_code, 4)


def test_does_not_inline_across_dependency_write():
    source_code = """
def validator(a: int) -> int:
    x = a + 1
    a = a + 2
    return x
"""

    assert script_size(source_code, 4) == script_size(
        source_code, 4, config=NO_INLINE_CONFIG
    )
    assert eval_uplc(source_code, 4, config=INLINE_CONFIG).value == 5


@pytest.mark.parametrize(
    "reader_setup",
    [
        """
    def reader() -> int:
        return a
""",
        """
    def read_a() -> int:
        return a
    reader = read_a
""",
        """
    def read_a() -> int:
        return a
    def reader() -> int:
        return read_a()
""",
    ],
)
def test_does_not_inline_across_captured_dependency_write(reader_setup):
    source_code = f"""
def validator(_: None) -> int:
    a = 1
{reader_setup}
    x = reader()
    a = 2
    return x
"""

    assert eval_uplc_value(source_code, Unit(), config=NO_INLINE_CONFIG) == 1
    assert eval_uplc_value(source_code, Unit(), config=INLINE_CONFIG) == 1


@pytest.mark.parametrize(
    "read_expression",
    [
        "return read_x() + x",
        "y = read_x()\n    return y + x",
    ],
)
def test_counts_captured_dependency_as_a_read(read_expression):
    source_code = f"""
def validator(_: None) -> int:
    x = 1
    def read_x() -> int:
        return x
    x = x + 1
    {read_expression}
"""

    assert eval_uplc_value(source_code, Unit(), config=NO_INLINE_CONFIG) == 4
    assert eval_uplc_value(source_code, Unit(), config=INLINE_CONFIG) == 4


def test_does_not_inline_into_short_circuit_branch():
    source_code = """
def validator(_: None) -> int:
    x = 1 // 0
    return 0 if True else x
"""

    with pytest.raises(RuntimeError):
        eval_uplc(source_code, Unit(), config=INLINE_CONFIG)


def test_does_not_inline_into_possibly_empty_comprehension():
    source_code = """
def validator(_: None) -> int:
    x = 1 // 0
    return sum([x for _ in range(0)])
"""

    with pytest.raises(RuntimeError):
        eval_uplc(source_code, Unit(), config=INLINE_CONFIG)


def test_does_not_inline_when_read_later():
    source_code = """
def validator(a: int) -> int:
    x = a + 1
    y = x
    return y + x
"""

    assert eval_uplc(source_code, 4, config=INLINE_CONFIG).value == 10


def test_does_not_cross_conditional_control_flow():
    source_code = """
x = 1 // 0
if condition:
    return_value = 1
return x
"""

    assert rewrite(source_code) == ast.dump(
        ast.parse(source_code), include_attributes=False
    )


def test_does_not_cross_loop_control_flow():
    source_code = """
def validator(a: int) -> int:
    x = 1 // 0
    while a > 0:
        return 1
    return x
"""

    with pytest.raises(RuntimeError):
        eval_uplc(source_code, 1, config=INLINE_CONFIG)


@pytest.mark.parametrize("loop", ["for i in range(2):", "while i < 2:"])
def test_does_not_inline_inside_loop(loop):
    source_code = f"""
def validator(a: int) -> int:
    i = 0
    s = 0
    {loop}
        x = a + i
        y = x
        s = s + y
        i = i + 1
    return s
"""

    assert script_size(source_code, 4) == script_size(
        source_code, 4, config=NO_INLINE_CONFIG
    )
