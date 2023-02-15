import frozendict
import hypothesis
import unittest

from uplc import ast as uplc, eval as uplc_eval
from hypothesis import example, given
from hypothesis import strategies as st

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
