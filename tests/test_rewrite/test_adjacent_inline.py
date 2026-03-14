import unittest

import pytest

import opshin.compiler as compiler
from opshin import builder
from opshin.util import NoOp
from tests.utils import DEFAULT_TEST_CONFIG, Unit, eval_uplc

INLINE_CONFIG = DEFAULT_TEST_CONFIG.update(adjacent_inline=True)


def script_size(source_code: str, *args, config=INLINE_CONFIG) -> int:
    builder._static_compile.cache_clear()
    return len(builder._build(builder._compile(source_code, *args, config=config)))


def script_size_without_adjacent_inline(source_code: str, *args, config=INLINE_CONFIG):
    original = compiler.RewriteAdjacentInline
    compiler.RewriteAdjacentInline = NoOp
    try:
        builder._static_compile.cache_clear()
        return len(builder._build(builder._compile(source_code, *args, config=config)))
    finally:
        compiler.RewriteAdjacentInline = original
        builder._static_compile.cache_clear()


class AdjacentInlineTest(unittest.TestCase):
    def test_inline_adjacent_return(self):
        source_code = """
def validator(a: int) -> int:
    x = a + 1
    return x
"""
        target_code = """
def validator(a: int) -> int:
    return a + 1
"""

        self.assertEqual(script_size(source_code, 4), script_size(target_code, 4))

    def test_inline_adjacent_chain(self):
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

        self.assertEqual(script_size(source_code, 4), script_size(target_code, 4))

    def test_inline_adjacent_return_in_branch(self):
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

        self.assertEqual(script_size(source_code, 4), script_size(target_code, 4))

    def test_inline_same_flow_non_adjacent_alias(self):
        source_code = """
def validator(a: int) -> int:
    x = a
    z = 1
    return x + z
"""
        target_code = """
def validator(a: int) -> int:
    z = 1
    return a + z
"""

        self.assertEqual(script_size(source_code, 4), script_size(target_code, 4))

    def test_inline_same_flow_non_adjacent_constant(self):
        source_code = """
def validator(_: None) -> int:
    x = 5
    z = 1
    return x + z
"""
        target_code = """
def validator(_: None) -> int:
    z = 1
    return 5 + z
"""

        self.assertEqual(script_size(source_code, Unit()), script_size(target_code, Unit()))

    def test_does_not_inline_non_adjacent_nontrivial_expression(self):
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

        self.assertEqual(
            script_size(source_code, 4),
            script_size(target_code, 4),
        )

    def test_does_not_inline_across_dependency_write(self):
        source_code = """
def validator(a: int) -> int:
    x = a + 1
    a = a + 2
    return x
"""

        self.assertEqual(
            script_size(source_code, 4),
            script_size_without_adjacent_inline(source_code, 4),
        )

    def test_does_not_inline_into_short_circuit(self):
        source_code = """
def validator(_: None) -> int:
    x = 1 // 0
    return 0 if True else x
"""

        with pytest.raises(RuntimeError):
            eval_uplc(source_code, Unit(), config=INLINE_CONFIG)

    def test_does_not_inline_when_read_later(self):
        source_code = """
def validator(a: int) -> int:
    x = a + 1
    y = x
    return y + x
"""

        self.assertEqual(eval_uplc(source_code, 4, config=INLINE_CONFIG).value, 10)

    def test_does_not_inline_inside_for_loop(self):
        source_code = """
def validator(a: int) -> int:
    s = 0
    for i in range(2):
        x = a + i
        y = x
        s = s + y
    return s
"""

        self.assertEqual(
            script_size(source_code, 4),
            script_size_without_adjacent_inline(source_code, 4),
        )

    def test_does_not_inline_inside_while_loop(self):
        source_code = """
def validator(a: int) -> int:
    s = 0
    i = 0
    while i < 2:
        x = a + i
        y = x
        s = s + y
        i = i + 1
    return s
"""

        self.assertEqual(
            script_size(source_code, 4),
            script_size_without_adjacent_inline(source_code, 4),
        )
