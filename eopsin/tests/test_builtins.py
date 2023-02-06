import frozendict
import hypothesis
import unittest

from uplc import ast as uplc, eval as uplc_eval
from hypothesis import example, given
from hypothesis import strategies as st
from parameterized import parameterized

from .. import compiler, prelude, type_inference


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class MiscTest(unittest.TestCase):
    @given(i=st.integers())
    @example(256)
    @example(0)
    def test_chr(self, i):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int) -> str:
    return chr(x)
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            i_unicode = chr(i).encode("utf8")
        except (ValueError, OverflowError):
            i_unicode = None
        try:
            for d in [uplc.PlutusInteger(i)]:
                f = uplc.Apply(f, d)
            ret = uplc_eval(f).value
        except Exception as e:
            ret = None
        self.assertEqual(ret, i_unicode, "chr returned wrong value")
