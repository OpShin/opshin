import frozendict
import hypothesis
import unittest

from uplc import ast as uplc, eval as uplc_eval
from hypothesis import example, given
from hypothesis import strategies as st
from parameterized import parameterized

from .. import compiler, prelude, type_inference


class OpTest(unittest.TestCase):
    @given(x=st.booleans(), y=st.booleans())
    def test_and_bool(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bool, y: bool) -> bool:
    return x and y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x)), uplc.PlutusInteger(int(y))]:
            f = uplc.Apply(f, d)
        ret = bool(uplc_eval(f).value)
        self.assertEqual(ret, x and y, "and returned wrong value")

    @given(x=st.booleans(), y=st.booleans())
    def test_or_bool(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bool, y: bool) -> bool:
    return x or y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x)), uplc.PlutusInteger(int(y))]:
            f = uplc.Apply(f, d)
        ret = bool(uplc_eval(f).value)
        self.assertEqual(ret, x or y, "or returned wrong value")

    @given(x=st.booleans())
    def test_not_bool(self, x):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bool) -> bool:
    return not x
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x))]:
            f = uplc.Apply(f, d)
        ret = bool(uplc_eval(f).value)
        self.assertEqual(ret, not x, "not returned wrong value")

    @given(x=st.integers())
    def test_usub_int(self, x):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int) -> int:
    return -x
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, -x, "not returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_add_int(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int, y: int) -> int:
    return x + y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x)), uplc.PlutusInteger(int(y))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, x + y, "+ returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_sub_int(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int, y: int) -> int:
    return x - y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x)), uplc.PlutusInteger(int(y))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, x - y, "- returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_mul_int(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int, y: int) -> int:
    return x * y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x)), uplc.PlutusInteger(int(y))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, x * y, "* returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_div_int(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int, y: int) -> int:
    return x // y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            exp = x // y
        except ZeroDivisionError:
            exp = None
        try:
            for d in [uplc.PlutusInteger(int(x)), uplc.PlutusInteger(int(y))]:
                f = uplc.Apply(f, d)
            ret = uplc_eval(f).value
        except Exception:
            ret = None
        self.assertEqual(ret, exp, "// returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_mod_int(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int, y: int) -> int:
    return x % y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            exp = x % y
        except ZeroDivisionError:
            exp = None
        try:
            for d in [uplc.PlutusInteger(int(x)), uplc.PlutusInteger(int(y))]:
                f = uplc.Apply(f, d)
            ret = uplc_eval(f).value
        except Exception:
            ret = None
        self.assertEqual(ret, exp, "% returned wrong value")

    @given(x=st.binary(), y=st.binary())
    def test_add_bytes(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bytes, y: bytes) -> bytes:
    return x + y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusByteString(bytes(x)), uplc.PlutusByteString(bytes(y))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, x + y, "+ returned wrong value")

    @given(x=st.text(), y=st.text())
    def test_add_str(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: str, y: str) -> str:
    return x + y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusByteString(bytes(x.encode("utf8"))),
            uplc.PlutusByteString(bytes(y.encode("utf8"))),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, x + y, "+ returned wrong value")

    @given(x=st.binary(), y=st.integers(), z=st.integers())
    @example(b"\x00", -2, 0)
    @example(b"1234", 1, 2)
    @example(b"1234", 2, 4)
    @example(b"1234", 2, 2)
    @example(b"1234", 3, 3)
    @example(b"1234", 3, 1)
    def test_slice_bytes(self, x, y, z):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bytes, y: int, z: int) -> bytes:
    return x[y:z]
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            exp = x[y:z]
        except IndexError:
            exp = None
        try:
            for d in [
                uplc.PlutusByteString(x),
                uplc.PlutusInteger(y),
                uplc.PlutusInteger(z),
            ]:
                f = uplc.Apply(f, d)
            ret = uplc_eval(f).value
        except:
            ret = None
        self.assertEqual(ret, exp, "byte slice returned wrong value")

    @given(x=st.binary(), y=st.integers())
    @example(b"1234", 0)
    @example(b"1234", 1)
    @example(b"1234", -1)
    def test_index_bytes(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bytes, y: int) -> int:
    return x[y]
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            exp = x[y]
        except IndexError:
            exp = None
        try:
            for d in [uplc.PlutusByteString(x), uplc.PlutusInteger(y)]:
                f = uplc.Apply(f, d)
            ret = uplc_eval(f).value
        except:
            ret = None
        self.assertEqual(ret, exp, "byte index returned wrong value")

    @given(xs=st.lists(st.integers()), y=st.integers())
    @example(xs=[0], y=-1)
    @example(xs=[0], y=0)
    def test_index_list(self, xs, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
from typing import Dict, List, Union
def validator(x: List[int], y: int) -> int:
    return x[y]
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            exp = xs[y]
        except IndexError:
            exp = None
        try:
            for d in [
                uplc.PlutusList([uplc.PlutusInteger(x) for x in xs]),
                uplc.PlutusInteger(y),
            ]:
                f = uplc.Apply(f, d)
            ret = uplc_eval(f).value
        except Exception as e:
            ret = None
        self.assertEqual(ret, exp, "list index returned wrong value")

    @given(xs=st.lists(st.integers()), y=st.integers())
    @example(xs=[0, 1], y=-1)
    @example(xs=[0, 1], y=0)
    def test_in_list_int(self, xs, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
from typing import Dict, List, Union
def validator(x: List[int], y: int) -> bool:
    return y in x
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = y in xs
        for d in [
            uplc.PlutusList([uplc.PlutusInteger(x) for x in xs]),
            uplc.PlutusInteger(y),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, exp, "list in returned wrong value")

    @given(xs=st.lists(st.binary()), y=st.binary())
    def test_in_list_bytes(self, xs, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
from typing import Dict, List, Union
def validator(x: List[bytes], y: bytes) -> bool:
    return y in x
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = y in xs
        for d in [
            uplc.PlutusList([uplc.PlutusByteString(x) for x in xs]),
            uplc.PlutusByteString(y),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, exp, "list in returned wrong value")

    @given(x=st.binary(), y=st.binary())
    def test_eq_bytes(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bytes, y: bytes) -> bool:
    return x == y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = x == y
        for d in [
            uplc.PlutusByteString(x),
            uplc.PlutusByteString(y),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, exp, "bytes eq returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_eq_bytes(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int, y: int) -> bool:
    return x == y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = x == y
        for d in [
            uplc.PlutusInteger(x),
            uplc.PlutusInteger(y),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, exp, "int eq returned wrong value")

    @given(x=st.text(), y=st.text())
    def test_eq_str(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: str, y: str) -> bool:
    return x == y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = x == y
        for d in [
            uplc.PlutusByteString(x.encode("utf8")),
            uplc.PlutusByteString(y.encode("utf8")),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, exp, "str eq returned wrong value")

    @given(x=st.booleans(), y=st.booleans())
    def test_eq_bool(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bool, y: bool) -> bool:
    return x == y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = x == y
        for d in [
            uplc.PlutusInteger(int(x)),
            uplc.PlutusInteger(int(y)),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, exp, "str eq returned wrong value")
