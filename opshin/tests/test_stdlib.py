import unittest

from hypothesis import example, given
from hypothesis import strategies as st
from uplc import ast as uplc, eval as uplc_eval

from .. import compiler


class StdlibTest(unittest.TestCase):
    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_keys(self, xs):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: Dict[int, bytes]) -> List[int]:
    return x.keys()
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusMap(
                {uplc.PlutusInteger(k): uplc.PlutusByteString(v) for k, v in xs.items()}
            )
        ]:
            f = uplc.Apply(f, d)
        ret = [x.value for x in uplc_eval(f).value]
        self.assertEqual(ret, list(xs.keys()), "dict.keys returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_values(self, xs):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: Dict[int, bytes]) -> List[bytes]:
    return x.values()
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusMap(
                {uplc.PlutusInteger(k): uplc.PlutusByteString(v) for k, v in xs.items()}
            )
        ]:
            f = uplc.Apply(f, d)
        ret = [x.value for x in uplc_eval(f).value]
        self.assertEqual(ret, list(xs.values()), "dict.keys returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_items_keys_sum(self, xs):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(xs: Dict[int, bytes]) -> int:
    sum_keys = 0
    for x in xs.items():
        sum_keys += x[0]
    return sum_keys
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusMap(
                {uplc.PlutusInteger(k): uplc.PlutusByteString(v) for k, v in xs.items()}
            )
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, sum(xs.keys()), "dict.items returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_items_values_sum(self, xs):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(xs: Dict[int, bytes]) -> bytes:
    sum_values = b""
    for x in xs.items():
        sum_values += x[1]
    return sum_values
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusMap(
                {uplc.PlutusInteger(k): uplc.PlutusByteString(v) for k, v in xs.items()}
            )
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, b"".join(xs.values()), "dict.items returned wrong value")

    @given(xs=st.text())
    def test_str_encode(self, xs):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: str) -> bytes:
    return x.encode()
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusByteString(xs.encode("utf8"))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, xs.encode(), "str.encode returned wrong value")

    @given(xs=st.binary())
    def test_str_decode(self, xs):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
def validator(x: bytes) -> str:
    return x.decode()
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        try:
            exp = xs.decode()
        except UnicodeDecodeError:
            exp = None
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusByteString(xs)]:
            f = uplc.Apply(f, d)
        try:
            ret = uplc_eval(f).value.decode("utf8")
        except UnicodeDecodeError:
            ret = None
        self.assertEqual(ret, exp, "bytes.decode returned wrong value")

    @given(xs=st.binary())
    @example(b"dc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2")
    def test_constant_bytestring(self, xs):
        source_code = f"""
def validator(x: None) -> bytes:
    return {repr(xs)}
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.BuiltinUnit()]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, xs, "literal bytes returned wrong value")

    @given(xs=st.integers())
    def test_constant_integer(self, xs):
        source_code = f"""
def validator(x: None) -> int:
    return {repr(xs)}
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.BuiltinUnit()]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, xs, "literal integer returned wrong value")

    @given(xs=st.text())
    def test_constant_string(self, xs):
        source_code = f"""
def validator(x: None) -> str:
    return {repr(xs)}
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.BuiltinUnit()]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value.decode("utf8")
        self.assertEqual(ret, xs, "literal string returned wrong value")

    def test_constant_unit(self):
        source_code = f"""
def validator(x: None) -> None:
    return None
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.BuiltinUnit()]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(ret, uplc.BuiltinUnit(), "literal None returned wrong value")

    @given(st.booleans())
    def test_constant_bool(self, x: bool):
        source_code = f"""
def validator(x: None) -> bool:
    return {repr(x)}
            """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.BuiltinUnit()]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value == 1
        self.assertEqual(ret, x, "literal bool returned wrong value")
