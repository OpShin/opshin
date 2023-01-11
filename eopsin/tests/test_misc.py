import unittest
from hypothesis import example, given, strategies as st

import uplc
from .. import compiler, type_inference


class MiscTest(unittest.TestCase):
    def test_assert_sum_contract_succeed(self):
        input_file = "examples/smart_contracts/assert_sum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(20), uplc.PlutusInteger(22), uplc.BuiltinUnit()]:
            f = uplc.Apply(f, d)
        ret = uplc.Machine(f).eval()
        self.assertEqual(ret, uplc.PlutusConstr(0, []))

    def test_assert_sum_contract_fail(self):
        input_file = "examples/smart_contracts/assert_sum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        try:
            f = code.term
            # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
            for d in [
                uplc.PlutusInteger(0),
                uplc.PlutusInteger(23),
                uplc.BuiltinUnit(),
            ]:
                f = uplc.Apply(f, d)
            ret = uplc.Machine(f).eval()
            self.fail("Machine did validate the content")
        except Exception as e:
            pass

    @given(
        a=st.integers(min_value=-10, max_value=10),
        b=st.integers(min_value=0, max_value=10),
    )
    def test_mult_contract(self, a: int, b: int):
        input_file = "examples/mult.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(a), uplc.PlutusInteger(b)]:
            f = uplc.Apply(f, d)
        ret = uplc.Machine(f).eval()
        self.assertEqual(ret, uplc.PlutusInteger(a * b))

    @given(
        a=st.integers(),
        b=st.integers(),
    )
    def test_sum_contract(self, a: int, b: int):
        input_file = "examples/sum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(a), uplc.PlutusInteger(b)]:
            f = uplc.Apply(f, d)
        ret = uplc.Machine(f).eval()
        self.assertEqual(ret, uplc.PlutusInteger(a + b))
