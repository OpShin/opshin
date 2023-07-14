import unittest

import cbor2
import hypothesis
import pycardano
from frozendict import frozendict
import frozenlist as fl
from hypothesis import example, given
from hypothesis import strategies as st
from uplc import ast as uplc, eval as uplc_eval
from uplc.ast import (
    PlutusMap,
    PlutusConstr,
    PlutusList,
    PlutusInteger,
    PlutusByteString,
)

from . import PLUTUS_VM_PROFILE
from .. import compiler

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)

from opshin.ledger.api_v2 import (
    FinitePOSIXTime,
    PosInfPOSIXTime,
    UpperBoundPOSIXTime,
    FalseData,
    TrueData,
)


def frozenlist(l):
    l = fl.FrozenList(l)
    l.freeze()
    return l


pos_int = st.integers(min_value=0, max_value=2**64 - 1)


uplc_data_integer = st.builds(PlutusInteger, st.integers())
uplc_data_bytestring = st.builds(PlutusByteString, st.binary())


def rec_data_strategies(uplc_data):
    uplc_data_list = st.builds(lambda x: PlutusList(frozenlist(x)), st.lists(uplc_data))
    uplc_data_constr = st.builds(
        lambda x, y: PlutusConstr(x, frozenlist(y)),
        pos_int,
        st.lists(uplc_data),
    )
    uplc_data_map = st.builds(
        PlutusMap,
        st.dictionaries(
            st.one_of(
                uplc_data_integer, uplc_data_bytestring
            ),  # TODO technically constr is legal too, but causes hashing error
            uplc_data,
            dict_class=frozendict,
        ),
    )
    return st.one_of(uplc_data_map, uplc_data_list, uplc_data_constr)


uplc_data = st.recursive(
    st.one_of(uplc_data_bytestring, uplc_data_integer),
    rec_data_strategies,
    max_leaves=4,
)

# TODO fix handling of these strings
formattable_text = st.from_regex(r"\A((?!['\\])[ -~])*\Z")


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

    @given(x=st.integers(), y=st.integers(min_value=0, max_value=20))
    def test_pow_int(self, x, y):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: int, y: int) -> int:
    return x ** y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x)), uplc.PlutusInteger(int(y))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, x**y, "** returned wrong value")

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
        self.assertEqual(ret, exp, "bool eq returned wrong value")

    @given(x=st.integers(min_value=0, max_value=150), y=st.text())
    def test_mul_int_str(self, x, y):
        source_code = """
def validator(x: int, y: str) -> str:
    return x * y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(int(x)), uplc.PlutusByteString(str(y).encode())]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode()
        self.assertEqual(ret, x * y, "* returned wrong value")

    @given(x=st.text(), y=st.integers(min_value=0, max_value=150))
    def test_mul_str_int(self, x, y):
        source_code = """
def validator(x: str, y: int) -> str:
    return x * y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusByteString(str(x).encode()), uplc.PlutusInteger(int(y))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode()
        self.assertEqual(ret, x * y, "* returned wrong value")

    @given(x=st.integers(min_value=0, max_value=150), y=st.binary())
    def test_mul_int_bytes(self, x, y):
        source_code = """
def validator(x: int, y: bytes) -> bytes:
    return x * y
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        exp = x * y
        for d in [
            uplc.PlutusInteger(int(x)),
            uplc.PlutusByteString(y),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, exp, "bytes int multiplication returned wrong value")

    @given(x=st.binary(), y=st.integers(min_value=0, max_value=150))
    def test_mul_bytes_int(self, x, y):
        source_code = """
def validator(x: bytes, y: int) -> bytes:
    return x * y
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying

        for d in [uplc.PlutusByteString(x), uplc.PlutusInteger(int(y))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, x * y, "* returned wrong value")

    @given(x=st.integers())
    def test_fmt_int(self, x):
        source_code = """
def validator(x: int) -> str:
    return f"{x}"
    """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        exp = f"{x}"
        for d in [
            uplc.PlutusInteger(int(x)),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, exp, "int string formatting returned wrong value")

    @given(x=st.booleans())
    def test_fmt_bool(self, x):
        source_code = """
def validator(x: bool) -> str:
    return f"{x}"
    """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        exp = f"{x}"
        for d in [
            uplc.PlutusInteger(int(x)),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, exp, "bool string formatting returned wrong value")

    @given(x=st.text())
    def test_fmt_str(self, x):
        source_code = """
def validator(x: str) -> str:
    return f"{x}"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{x}"
        for d in [
            uplc.PlutusByteString(x.encode("utf8")),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, exp, "string string formatting returned wrong value")

    @given(x=st.binary())
    @example(b"'")
    @example(b'"')
    @example(b"\\")
    @example(b"\r")
    @example(b"\n")
    @example(b"\t")
    @example(b"\x7f")
    def test_fmt_bytes(self, x):
        source_code = """
def validator(x: bytes) -> str:
    return f"{x}"
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        exp = f"{x}"
        for d in [
            uplc.PlutusByteString(x),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        if b"'" not in x:
            self.assertEqual(ret, exp, "bytes string formatting returned wrong value")
        else:
            # NOTE: formally this is a bug where we do not have the same semantics as python
            # specifically when ' is contained in the string we do not change the quotation marks
            self.assertEqual(
                eval(ret), x, "bytes string formatting returned wrong value"
            )

    @given(x=st.none())
    def test_fmt_none(self, x):
        source_code = """
def validator(x: None) -> str:
    return f"{x}"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{x}"
        for d in [
            uplc.PlutusConstr(0, []),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, exp, "none string formatting returned wrong value")

    @given(
        x=st.builds(
            UpperBoundPOSIXTime,
            st.one_of(
                st.builds(FinitePOSIXTime, st.integers()), st.builds(PosInfPOSIXTime)
            ),
            st.one_of(st.builds(TrueData), st.builds(FalseData)),
        )
    )
    @example(UpperBoundPOSIXTime(PosInfPOSIXTime(), TrueData()))
    def test_fmt_dataclass(self, x: UpperBoundPOSIXTime):
        source_code = """
from opshin.prelude import *

def validator(x: UpperBoundPOSIXTime) -> str:
    return f"{x}"
            """

        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{x}"
        for d in [
            uplc.data_from_cbor(x.to_cbor()),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(
            ret, exp, "several element string formatting returned wrong value"
        )

    @given(x=st.integers(), y=st.integers())
    def test_fmt_multiple(self, x, y):
        source_code = """
def validator(x: int, y: int) -> str:
    return f"a{x}b{y}c"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"a{x}b{y}c"
        for d in [
            uplc.PlutusInteger(x),
            uplc.PlutusInteger(y),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(
            ret, exp, "several element string formatting returned wrong value"
        )

    @given(x=st.lists(st.integers()))
    @example([])
    @example([0])
    def test_fmt_tuple_int(self, x):
        params = [f"a{i}" for i in range(len(x))]
        source_code = f"""
def validator({",".join(p + ": int" for p in params)}) -> str:
    return f"{{({"".join(p + "," for p in params)})}}"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{tuple(x)}"
        for d in (
            [uplc.PlutusInteger(xi) for xi in x] if x else [uplc.PlutusConstr(0, [])]
        ):
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(
            ret, exp, "integer tuple string formatting returned wrong value"
        )

    @given(x=st.lists(formattable_text))
    def test_fmt_tuple_str(self, x):
        # TODO strings are not properly escaped here
        params = [f"a{i}" for i in range(len(x))]
        source_code = f"""
def validator({",".join(p + ": str" for p in params)}) -> str:
    return f"{{({"".join(p + "," for p in params)})}}"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{tuple(x)}"
        for d in (
            [uplc.PlutusByteString(xi.encode("utf8")) for xi in x]
            if x
            else [uplc.PlutusConstr(0, [])]
        ):
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, exp, "tuple string formatting returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_fmt_pair_int(self, x, y):
        source_code = f"""
def validator(x: int, y: int) -> str:
    a = ""
    for p in {{x:y}}.items():
        a = f"{{p}}"
    return a
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{(x, y)}"
        for d in [
            uplc.PlutusInteger(x),
            uplc.PlutusInteger(y),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(
            ret, exp, "integer tuple string formatting returned wrong value"
        )

    @given(x=formattable_text, y=formattable_text)
    def test_fmt_pair_str(self, x, y):
        # TODO strings are not properly escaped here
        source_code = f"""
def validator(x: str, y: str) -> str:
    a = ""
    for p in {{x:y}}.items():
        a = f"{{p}}"
    return a
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{(x, y)}"
        for d in [
            uplc.PlutusByteString(x.encode("utf8")),
            uplc.PlutusByteString(y.encode("utf8")),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(
            ret, exp, "string tuple string formatting returned wrong value"
        )

    @given(xs=st.lists(formattable_text))
    @example([])
    @example(["x"])
    def test_fmt_list_str(self, xs):
        # TODO strings are not properly escaped here
        source_code = """
from opshin.prelude import *

def validator(x: List[str]) -> str:
    return f"{x}"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{list(xs)}"
        for d in [
            uplc.PlutusList([uplc.PlutusByteString(x.encode("utf8")) for x in xs])
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, exp, "string list string formatting returned wrong value")

    @given(xs=st.lists(st.integers()))
    @example([])
    @example([0])
    def test_fmt_list_int(self, xs):
        source_code = """
from opshin.prelude import *

def validator(x: List[int]) -> str:
    return f"{x}"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{list(xs)}"
        for d in [uplc.PlutusList([uplc.PlutusInteger(x) for x in xs])]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(
            ret, exp, "integer list string formatting returned wrong value"
        )

    @given(xs=st.dictionaries(formattable_text, st.integers()))
    @example(dict())
    @example({"": 0})
    def test_fmt_dict_int(self, xs):
        # TODO strings are not properly escaped here
        source_code = """
from opshin.prelude import *

def validator(x: Dict[str, int]) -> str:
    return f"{x}"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{dict(xs)}"
        for d in [
            uplc.PlutusMap(
                {
                    uplc.PlutusByteString(k.encode("utf8")): uplc.PlutusInteger(v)
                    for (k, v) in xs.items()
                }
            )
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, exp, "dict string formatting returned wrong value")

    @given(x=uplc_data)
    @example(PlutusConstr(0, [PlutusByteString(b"'")]))
    def test_fmt_any(self, x):
        x_data = pycardano.RawPlutusData(cbor2.loads(uplc.plutus_cbor_dumps(x)))
        source_code = """
def validator(x: Anything) -> str:
    return f"{x}"
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        exp = f"{x_data}"
        for d in [x]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        if "\\'" in ret:
            RawPlutusData = pycardano.RawPlutusData
            CBORTag = cbor2.CBORTag
            self.assertEqual(
                eval(ret), x_data, "raw cbor string formatting returned wrong value"
            )
        else:
            self.assertEqual(
                ret, exp, "raw cbor string formatting returned wrong value"
            )
