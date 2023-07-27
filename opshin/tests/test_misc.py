import xml.etree.ElementTree

import unittest

import frozendict
import hypothesis
from hypothesis import given
from hypothesis import strategies as st
from parameterized import parameterized
from uplc import ast as uplc, eval as uplc_eval

from . import PLUTUS_VM_PROFILE
from .. import compiler, prelude

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)

# these imports are required to eval the result of script context dumps
from ..ledger.api_v2 import *
from pycardano import RawPlutusData
from cbor2 import CBORTag


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int


@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int


a_or_b = st.sampled_from([A(0), B(1, 2)])
some_output = st.sampled_from([SomeOutputDatum(b"0"), SomeOutputDatumHash(b"1")])


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
        ret = uplc_eval(f)
        self.assertEqual(ret, uplc.PlutusConstr(0, []))

    @unittest.expectedFailure
    def test_assert_sum_contract_fail(self):
        input_file = "examples/smart_contracts/assert_sum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusInteger(0),
            uplc.PlutusInteger(23),
            uplc.BuiltinUnit(),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)

    @given(
        a=st.integers(min_value=-10, max_value=10),
        b=st.integers(min_value=0, max_value=10),
    )
    def test_mult_for(self, a: int, b: int):
        input_file = "examples/mult_for.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(a), uplc.PlutusInteger(b)]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(ret, uplc.PlutusInteger(a * b))

    @given(
        a=st.integers(min_value=-10, max_value=10),
        b=st.integers(min_value=0, max_value=10),
    )
    def test_mult_while(self, a: int, b: int):
        input_file = "examples/mult_while.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(a), uplc.PlutusInteger(b)]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(ret, uplc.PlutusInteger(a * b))

    @given(
        a=st.integers(),
        b=st.integers(),
    )
    def test_sum(self, a: int, b: int):
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
        ret = uplc_eval(f)
        self.assertEqual(ret, uplc.PlutusInteger(a + b))

    def test_complex_datum_correct_vals(self):
        input_file = "examples/complex_datum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.data_from_cbor(
                bytes.fromhex(
                    "d8799fd8799fd8799f581c81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acfffd8799fd8799fd8799f581c145db8343296bd214dde862a64d700c29ed8a71d58bcf865659f5463ffffffffd8799fd8799f581c81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acfffd8799fd8799fd8799f581c145db8343296bd214dde862a64d700c29ed8a71d58bcf865659f5463ffffffffd87a80d8799f1a38220b0bff1a001e84801a001e8480582051176daeee7f2ce62963c50a16f641951e21b8522da262980d4dd361a9bf331b4e4d7565736c69537761705f414d4dff"
                )
            )
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(
            uplc.PlutusByteString(
                bytes.fromhex(
                    "81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acf"
                )
            ),
            ret,
        )

    def test_hello_world(self):
        input_file = "examples/hello_world.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusConstr(0, [])]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)

    def test_list_datum_correct_vals(self):
        input_file = "examples/list_datum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.data_from_cbor(bytes.fromhex("d8799f9f41014102ffff"))]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(
            uplc.PlutusInteger(1),
            ret,
        )

    def test_showcase(self):
        input_file = "examples/showcase.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(1)]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(
            uplc.PlutusInteger(42),
            ret,
        )

    @given(n=st.integers(min_value=0, max_value=5))
    def test_fib_iter(self, n):
        input_file = "examples/fib_iter.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(n)]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(
            uplc.PlutusInteger(fib(n)),
            ret,
        )

    @given(n=st.integers(min_value=0, max_value=5))
    def test_fib_rec(self, n):
        input_file = "examples/fib_rec.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [uplc.PlutusInteger(n)]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(
            uplc.PlutusInteger(fib(n)),
            ret,
        )

    def test_gift_contract_succeed(self):
        input_file = "examples/smart_contracts/gift.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusConstr(
                0,
                [
                    uplc.PlutusByteString(
                        bytes.fromhex(
                            "dc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2"
                        )
                    )
                ],
            ),
            uplc.PlutusConstr(0, []),
            uplc.data_from_cbor(
                bytes.fromhex(
                    (
                        "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a1401a000f4240d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87a9f1b000001836ac117d8ffd87a80ffd8799fd87b80d87a80ffff9f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffa1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820c17c32f6433ae22c2acaebfb796bbfaee3993ff7ebb58a2bac6b4a3bdd2f6d28ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff"
                    )
                )
            ),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(ret, uplc.PlutusConstr(0, []))

    @unittest.expectedFailure
    def test_gift_contract_fail(self):
        input_file = "examples/smart_contracts/gift.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        # required sig missing int this script context
        for d in [
            uplc.PlutusConstr(
                0,
                [
                    uplc.PlutusByteString(
                        bytes.fromhex(
                            "dc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2"
                        )
                    )
                ],
            ),
            uplc.PlutusConstr(0, []),
            uplc.data_from_cbor(
                bytes.fromhex(
                    (
                        "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87a9f1b000001836ac117d8ffd87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820797a1e1720b63621c6b185088184cb8e23af6e46b55bd83e7a91024c823a6c2affffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff"
                    )
                )
            ),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)

    def test_recursion(self):
        source_code = """
def validator(_: None) -> int:
    def a(n: int) -> int:
      if n == 0:
        res = 0
      else:
        res = a(n-1)
      return res
    b = a
    def a(x: int) -> int:
      return 100
    return b(1)
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        for d in [
            uplc.PlutusConstr(0, []),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(uplc.PlutusInteger(100), ret)

    def test_datum_cast(self):
        input_file = "examples/datum_cast.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # Note that this passes even though we pass in a "wrong" datum - the cast only changes the type, it does not do any checks for correctness
        for d in [
            uplc.data_from_cbor(
                bytes.fromhex(
                    "d8799fd8799fd8799f581c81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acfffd8799fd8799fd8799f581c145db8343296bd214dde862a64d700c29ed8a71d58bcf865659f5463ffffffffd8799fd8799f581c81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acfffd8799fd8799fd8799f581c145db8343296bd214dde862a64d700c29ed8a71d58bcf865659f5463ffffffffd87a80d8799f1a38220b0bff1a001e84801a001e8480582051176daeee7f2ce62963c50a16f641951e21b8522da262980d4dd361a9bf331b4e4d7565736c69537761705f414d4dff"
                )
            ),
            uplc.PlutusByteString(b"test"),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(
            uplc.PlutusByteString(
                bytes.fromhex(
                    "81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acf"
                )
                + b"test"
            ),
            ret,
        )

    def test_wrapping_contract_compile(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/wrapped_token.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, force_three_params=True)
        code = code.compile()
        f = code.term

    def test_dual_use_compile(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/dual_use.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, force_three_params=True)
        code = code.compile()
        f = code.term

    def test_marketplace_compile(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/marketplace.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term

    def test_marketplace_compile_fail(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/marketplace.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        try:
            code = compiler.compile(ast, force_three_params=True)
            self.fail(
                "Allowed to compile an incompatible contract with three parameters"
            )
        except Exception:
            pass

    def test_parameterized_compile(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/parameterized.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term

    @unittest.expectedFailure
    def test_dict_datum(self):
        input_file = "examples/dict_datum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        # required sig missing int this script context
        for d in [
            uplc.PlutusConstr(
                0,
                [
                    uplc.PlutusMap(
                        frozendict.frozendict(
                            {uplc.PlutusConstr(0, [uplc.PlutusByteString(b"\x01")]): 2}
                        )
                    )
                ],
            ),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)

    @unittest.expectedFailure
    def test_overopt_removedeadvar(self):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    a = x.policy_id
    return True
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusConstr(0, []),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)

    @unittest.expectedFailure
    def test_opt_shared_var(self):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
        source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    if False:
        y = x
    else:
        a = y
    return True
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusConstr(0, []),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)

    def test_list_expr(self):
        # this tests that the list expression is evaluated correctly
        source_code = """
def validator(x: None) -> List[int]:
    return [1, 2, 3, 4, 5]
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusConstr(0, []),
        ]:
            f = uplc.Apply(f, d)
        ret = [x.value for x in uplc_eval(f).value]
        self.assertEqual(ret, [1, 2, 3, 4, 5], "List expression incorrectly compiled")

    def test_list_expr_not_const(self):
        # this tests that the list expression is evaluated correctly (for non-constant expressions)
        source_code = """
def validator(x: int) -> List[int]:
    return [x, x+1, x+2, x+3, x+4]
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusInteger(1),
        ]:
            f = uplc.Apply(f, d)
        ret = [x.value for x in uplc_eval(f).value]
        self.assertEqual(ret, [1, 2, 3, 4, 5], "List expression incorrectly compiled")

    def test_dict_expr_not_const(self):
        # this tests that the list expression is evaluated correctly (for non-constant expressions)
        source_code = """
def validator(x: int) -> Dict[int, bytes]:
    return {x: b"a", x+1: b"b"}
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusInteger(1),
        ]:
            f = uplc.Apply(f, d)
        ret = {x.value: y.value for x, y in uplc_eval(f).value.items()}
        self.assertEqual(
            ret, {1: b"a", 2: b"b"}, "Dict expression incorrectly compiled"
        )

    def test_redefine_poly_constr(self):
        # this tests that classes defined by assignment inherit constructors
        source_code = """
def validator(x: None) -> bytes:
    a = bytes
    return a([2, 3])
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusConstr(0, []),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, bytes([2, 3]), "Re-assignment of global variable failed")

    @given(st.booleans())
    def test_redefine_constr(self, x):
        # this tests that classes defined by assignment inherit constructors
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int
    bar: int
    
def validator(x: int) -> int:
    a = A
    return a(x, 1).foo
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusInteger(int(x)),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(ret, int(x), "Re-assignment of class constr failed")

    def test_wrap_into_generic_data(self):
        # this tests data is wrapped into Anything if a function accepts Anything
        source_code = """
from opshin.prelude import *
def validator(_: None) -> SomeOutputDatum:
    return SomeOutputDatum(b"a")
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusConstr(0, []),
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f)
        self.assertEqual(
            ret,
            uplc.data_from_cbor(prelude.SomeOutputDatum(b"a").to_cbor()),
            "Wrapping to generic data failed",
        )

    def test_list_comprehension_even(self):
        input_file = "examples/list_comprehensions.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusInteger(8),
            uplc.PlutusInteger(1),
        ]:
            f = uplc.Apply(f, d)
        ret = [x.value for x in uplc_eval(f).value]
        self.assertEqual(
            ret,
            [x * x for x in range(8) if x % 2 == 0],
            "List comprehension with filter incorrectly evaluated",
        )

    def test_list_comprehension_all(self):
        input_file = "examples/list_comprehensions.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusInteger(8),
            uplc.PlutusInteger(0),
        ]:
            f = uplc.Apply(f, d)
        ret = [x.value for x in uplc_eval(f).value]
        self.assertEqual(
            ret,
            [x * x for x in range(8)],
            "List comprehension incorrectly evaluated",
        )

    @hypothesis.given(some_output)
    def test_union_type_attr_access_all_records(self, x):
        source_code = """
from opshin.prelude import *

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: SomeOutputDatumHash
    
@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foo: SomeOutputDatum

def validator(x: Union[A, B]) -> Union[SomeOutputDatumHash, SomeOutputDatum]:
    return x.foo
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

        @dataclass()
        class A(PlutusData):
            CONSTR_ID = 0
            foo: SomeOutputDatumHash

        @dataclass()
        class B(PlutusData):
            CONSTR_ID = 1
            foo: SomeOutputDatum

        x = A(x) if isinstance(x, SomeOutputDatumHash) else B(x)

        res = uplc_eval(
            uplc.Apply(code, uplc.data_from_cbor(x.to_cbor())),
        )
        self.assertEqual(res, uplc.data_from_cbor(x.foo.to_cbor()))

    @hypothesis.given(some_output, st.sampled_from([1, 2, 3]))
    def test_union_type_attr_access_all_records_diff_pos(self, x, y):
        source_code = """
from opshin.prelude import *

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: SomeOutputDatumHash

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foo: SomeOutputDatum
    
@dataclass()
class C(PlutusData):
    CONSTR_ID = 2
    bar: int
    foo: SomeOutputDatum
    
@dataclass()
class D(PlutusData):
    CONSTR_ID = 3
    foobar: int
    bar: int
    foo: SomeOutputDatum

def validator(x: Union[A, B, C, D]) -> Union[SomeOutputDatumHash, SomeOutputDatum]:
    return x.foo
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

        @dataclass()
        class A(PlutusData):
            CONSTR_ID = 0
            foo: SomeOutputDatumHash

        @dataclass()
        class B(PlutusData):
            CONSTR_ID = 1
            foo: SomeOutputDatum

        @dataclass()
        class C(PlutusData):
            CONSTR_ID = 2
            bar: int
            foo: SomeOutputDatum

        @dataclass()
        class D(PlutusData):
            CONSTR_ID = 3
            foobar: int
            bar: int
            foo: SomeOutputDatum

        x = (
            A(x)
            if isinstance(x, SomeOutputDatumHash)
            else B(x)
            if y == 1
            else C(0, x)
            if y == 2
            else D(0, 0, x)
        )

        res = uplc_eval(
            uplc.Apply(code, uplc.data_from_cbor(x.to_cbor())),
        )
        self.assertEqual(res, uplc.data_from_cbor(x.foo.to_cbor()))

    @unittest.expectedFailure
    def test_union_type_all_records_same_constr(self):
        source_code = """
from opshin.prelude import *

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: SomeOutputDatumHash

@dataclass()
class B(PlutusData):
    CONSTR_ID = 0
    foo: SomeOutputDatum

def validator(x: Union[A, B]) -> Union[SomeOutputDatumHash, SomeOutputDatum]:
    return x.foo
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)

    @unittest.expectedFailure
    def test_union_type_attr_access_all_records_same_constr(self):
        source_code = """
from opshin.prelude import *

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: Token

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foo: Address

def validator(x: Union[A, B]) -> int:
    m = x.foo
    if isinstance(m, Address):
        k = 0
    else:
        k = 1
    return k
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)

    def test_union_type_attr_access_maximum_type(self):
        source_code = """
from opshin.prelude import *

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foo: int

def validator(x: Union[A, B]) -> int:
    return x.foo
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    def test_union_type_attr_anytype(self):
        source_code = """
from opshin.prelude import *

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: str

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foo: int

def validator(x: Union[A, B]) -> Anything:
    return x.foo
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)

    def test_typecast_anything_int(self):
        source_code = """
def validator(x: Anything) -> int:
    b: int = x
    return b
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0))).value
        self.assertEqual(res, 0)

    def test_typecast_int_anything(self):
        # this should compile, it happens implicitly anyways when calling a function with Any parameters
        source_code = """
def validator(x: int) -> Anything:
    b: Anything = x
    return b
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0))).value
        self.assertEqual(res, 0)

    def test_typecast_int_anything_int(self):
        source_code = """
def validator(x: int) -> Anything:
    b: Anything = x
    c: int = b
    return c + 1
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0))).value
        self.assertEqual(res, 1)

    def test_typecast_anything_int_anything(self):
        source_code = """
def validator(x: Anything) -> Anything:
    b: int = x
    c: Anything = b + 1
    return c
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0))).value
        self.assertEqual(res, 1)

    @unittest.expectedFailure
    def test_typecast_int_str(self):
        # this should compile, the two types are unrelated and there is no meaningful way to cast them either direction
        source_code = """
def validator(x: int) -> str:
    b: str = x
    return b
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)

    def test_typecast_int_int(self):
        source_code = """
def validator(x: int) -> int:
    b: int = x
    return b
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0))).value
        self.assertEqual(res, 0)

    def test_zero_ary(self):
        source_code = """
def a() -> None:
    assert False, "Executed a"

def validator(x: None) -> int:
    b = a
    if False:
        b()
    return 2
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0)))
        self.assertEqual(res.value, 2, "Invalid return value")

    @unittest.expectedFailure
    def test_zero_ary_exec(self):
        source_code = """
def a() -> None:
    assert False, "Executed a"

def validator(x: None) -> None:
    b = a
    if True:
        b()
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0)))

    def test_zero_ary_method(self):
        source_code = """
def validator(x: None) -> None:
    b = b"\\xFF".decode
    if False:
        b()
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0)))

    @unittest.expectedFailure
    def test_zero_ary_method_exec(self):
        source_code = """
def validator(x: None) -> None:
    b = b"\\xFF".decode
    if True:
        b()
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0)))

    def test_zero_ary_method_exec_suc(self):
        source_code = """
def validator(x: None) -> str:
    b = b"\\x32".decode
    return b()
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0)))
        self.assertEqual(res.value, b"\x32")

    def test_return_anything(self):
        source_code = """
from opshin.prelude import *

def validator() -> Anything:
    return b""
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(res, uplc.PlutusByteString(b""))

    def test_no_return_annotation(self):
        source_code = """
from opshin.prelude import *

def validator():
    return b""
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(res, uplc.PlutusByteString(b""))

    def test_no_parameter_annotation(self):
        source_code = """
from opshin.prelude import *

def validator(a) -> bytes:
    b: bytes = a
    return b
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusByteString(b"")))
        self.assertEqual(res, uplc.PlutusByteString(b""))

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_items_values_deconstr(self, xs):
        # asserts that deconstruction of parameters works for for loops too
        source_code = """
def validator(xs: Dict[int, bytes]) -> bytes:
    sum_values = b""
    for _, x in xs.items():
        sum_values += x
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
        self.assertEqual(
            ret,
            b"".join(xs.values()),
            "for loop deconstruction did not behave as expected",
        )

    def test_nested_deconstruction(self):
        source_code = """
def validator(xs) -> int:
    a, ((b, c), d) = (1, ((2, 3), 4))
    return a + b + c + d
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        f = uplc.Apply(f, uplc.PlutusConstr(0, []))
        ret = uplc_eval(f).value
        self.assertEqual(
            ret,
            1 + 2 + 3 + 4,
            "for loop deconstruction did not behave as expected",
        )

    @given(
        xs=st.dictionaries(
            st.binary(),
            st.dictionaries(st.binary(), st.integers(), max_size=3),
            max_size=5,
        )
    )
    def test_dict_items_values_deconstr(self, xs):
        # nested deconstruction with a Value-like object
        source_code = """
def validator(xs: Dict[bytes, Dict[bytes, int]]) -> int:
    sum_values = 0
    for pid, tk_dict in xs.items():
        for tk_name, tk_amount in tk_dict.items():
            sum_values += tk_amount
    return sum_values
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        for d in [
            uplc.PlutusMap(
                {
                    uplc.PlutusByteString(k): uplc.PlutusMap(
                        {
                            uplc.PlutusByteString(k2): uplc.PlutusInteger(v2)
                            for k2, v2 in v.items()
                        }
                    )
                    for k, v in xs.items()
                }
            )
        ]:
            f = uplc.Apply(f, d)
        ret = uplc_eval(f).value
        self.assertEqual(
            ret,
            sum(v for pid, d in xs.items() for nam, v in d.items()),
            "for loop deconstruction did not behave as expected",
        )

    def test_no_return_annotation_no_return(self):
        source_code = """
from opshin.prelude import *

def validator(a):
    pass
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(res, uplc.PlutusConstr(0, []))

    def test_opt_unsafe_cast(self):
        # test that unsafe casts are not optimized away
        source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    b: Anything = x
    a: int = b
    return True
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            for d in [
                uplc.PlutusConstr(0, []),
            ]:
                f = uplc.Apply(f, d)
            ret = uplc_eval(f)
            failed = False
        except Exception as e:
            failed = True
        self.assertTrue(failed, "Machine did validate the content")

    def test_constant_folding(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> bytes:
    return bytes.fromhex("0011")
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(res, uplc.PlutusByteString(bytes.fromhex("0011")))

    @unittest.expectedFailure
    def test_constant_folding_disabled(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> bytes:
    return bytes.fromhex("0011")
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=False).compile()

    def test_constant_folding_list(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> List[int]:
    return list(range(0, 10, 2))
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        self.assertIn("(con list<integer> [0, 2, 4, 6, 8])", code.dumps())
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(
            res, uplc.PlutusList([uplc.PlutusInteger(i) for i in range(0, 10, 2)])
        )

    def test_constant_folding_dict(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> Dict[str, bool]:
    return {"s": True, "m": False}
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        self.assertIn(
            "(con list<pair<data, data>> [[#4173, #01], [#416d, #00]]))", code.dumps()
        )
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(
            res,
            uplc.PlutusMap(
                {
                    uplc.PlutusByteString("s".encode()): uplc.PlutusInteger(1),
                    uplc.PlutusByteString("m".encode()): uplc.PlutusInteger(0),
                }
            ),
        )

    def test_constant_folding_complex(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> Dict[str, List[Dict[bytes, int]]]:
    return {"s": [{b"": 0}, {b"0": 1}]}
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(
            res,
            uplc.PlutusMap(
                {
                    uplc.PlutusByteString("s".encode()): uplc.PlutusList(
                        [
                            uplc.PlutusMap(
                                {uplc.PlutusByteString(b""): uplc.PlutusInteger(0)}
                            ),
                            uplc.PlutusMap(
                                {uplc.PlutusByteString(b"0"): uplc.PlutusInteger(1)}
                            ),
                        ]
                    ),
                }
            ),
        )

    def test_constant_folding_plutusdata(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> PubKeyCredential:
    return PubKeyCredential(bytes.fromhex("0011"))
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        self.assertIn("(con data #d8799f420011ff)", code.dumps())
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(
            res,
            uplc.PlutusConstr(
                constructor=0, fields=[uplc.PlutusByteString(value=b"\x00\x11")]
            ),
        )

    def test_constant_folding_user_def(self):
        source_code = """
def fib(i: int) -> int:
    return i if i < 2 else fib(i-1) + fib(i-2)

def validator(_: None) -> int:
    return fib(10)
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        self.assertIn("(con integer 55)", code.dumps())
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(
            res.value,
            55,
        )

    @unittest.expectedFailure
    def test_constant_folding_ifelse(self):
        source_code = """
def validator(_: None) -> int:
    if False:
        a = 10
    return a
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))

    @unittest.expectedFailure
    def test_constant_folding_for(self):
        source_code = """
def validator(x: List[int]) -> int:
    for i in x:
        a = 10
    return a
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusList([])))

    @unittest.expectedFailure
    def test_constant_folding_for_target(self):
        source_code = """
def validator(x: List[int]) -> int:
    for i in x:
        a = 10
    return i
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusList([])))

    @unittest.expectedFailure
    def test_constant_folding_while(self):
        source_code = """
def validator(_: None) -> int:
    while False:
        a = 10
    return a
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))

    @unittest.skip("Fine from a guarantee perspective, but needs better inspection")
    def test_constant_folding_guaranteed_branch(self):
        source_code = """
def validator(_: None) -> int:
    if False:
        a = 20
        b = 2 * a
    else:
        b = 2
    return b
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertIn("(con integer 40)", code.dumps())

    @unittest.skip("Fine from a guarantee perspective, but needs better inspection")
    def test_constant_folding_scoping(self):
        source_code = """
a = 4
def validator(_: None) -> int:
    a = 2
    b = 5 * a
    return b
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertIn("(con integer 10)", code.dumps())

    @unittest.skip("Fine from a guarantee perspective, but needs better inspection")
    def test_constant_folding_no_scoping(self):
        source_code = """
def validator(_: None) -> int:
    a = 4
    a = 2
    b = 5 * a
    return b
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertIn("(con integer 10)", code.dumps())

    def test_constant_folding_repeated_assign(self):
        source_code = """
def validator(i: int) -> int:
    a = 4
    for k in range(i):
        a = 2
    return a
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0)))
        self.assertEqual(res.value, 4)
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(1)))
        self.assertEqual(res.value, 2)

    def test_constant_folding_math(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> int:
    return 2 ** 10
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        code_src = code.dumps()
        self.assertIn(f"(con integer {2**10})", code_src)

    def test_constant_folding_ignore_reassignment(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> int:
    def int(a) -> int:
        return 2
    return int(5)
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(res, uplc.PlutusInteger(2))

    def test_constant_folding_no_print_eval(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> None:
    return print("hello")
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast, constant_folding=True).compile()
        code_src = code.dumps()
        self.assertIn(f'(con string "hello")', code_src)

    def test_inner_outer_state_functions(self):
        source_code = """
a = 2
def b() -> int:
    return a

def validator(_: None) -> int:
    a = 3
    return b()
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(res, uplc.PlutusInteger(2))

    def test_inner_outer_state_functions_nonglobal(self):
        source_code = """

def validator(_: None) -> int:
    a = 2
    def b() -> int:
        return a
    def c() -> int:
        a = 3
        return b()
    return c()
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(res, uplc.PlutusInteger(2))

    def test_outer_state_change_functions(self):
        source_code = """
a = 2
def b() -> int:
    return a
a = 3

def validator(_: None) -> int:
    return b()
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))
        self.assertEqual(res, uplc.PlutusInteger(3))

    @unittest.expectedFailure
    def test_failing_annotated_type(self):
        source_code = """
def c():
    a = 2
    def b() -> int:
        return a
    return b

def validator(_: None):
    a = 3
    return c()
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    @unittest.expectedFailure
    def test_access_enclosing_variable_before_def(self):
        # note this is a runtime error, just like it would be in python!
        source_code = """
a = "1"
def validator(_: None) -> None:
   def d() -> str:
       return a
   print(d())
   a = "2"
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))

    @unittest.expectedFailure
    def test_access_local_variable_before_assignment(self):
        # note this is a runtime error, just like it would be in python!
        source_code = """
a = "1"
def validator(_: None) -> None:
   print(a)
   a = "2"
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))

    def test_warn_bytestring(self):
        # note this is a runtime error, just like it would be in python!
        source_code = """
b = b"0011ff"
def validator(_: None) -> None:
    pass
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusConstr(0, [])))

    @parameterized.expand(
        [
            (
                "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87980d87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820746957f0eb57f2b11119684e611a98f373afea93473fefbb7632d579af2f6259ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff"
            ),
            (
                "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87a9f1b000001836ac117d8ffd87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820797a1e1720b63621c6b185088184cb8e23af6e46b55bd83e7a91024c823a6c2affffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff"
            ),
            (
                "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a1401a000f4240d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87a9f1b000001836ac117d8ffd87a80ffd8799fd87b80d87a80ffff9f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffa1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820c17c32f6433ae22c2acaebfb796bbfaee3993ff7ebb58a2bac6b4a3bdd2f6d28ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff"
            ),
        ]
    )
    def test_script_context_str_format(self, p: str):
        context = ScriptContext.from_cbor(bytes.fromhex(p))
        expected = f"{context}"

        source_code = """
from opshin.prelude import *

def validator(c: ScriptContext) -> str:
    return f"{c}"
        """
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(
            uplc.Apply(code, uplc.data_from_cbor(context.to_cbor()))
        ).value.decode("utf8")
        # should not raise
        eval(res)

    @hypothesis.given(st.binary(), st.binary())
    def test_uplc_builtin(self, x, y):
        # note this is a runtime error, just like it would be in python!
        source_code = """
from opshin.std.builtins import *
def validator(x: bytes, y: bytes) -> bytes:
    return append_byte_string(x, y)
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(
            uplc.Apply(
                uplc.Apply(code, uplc.PlutusByteString(x)), uplc.PlutusByteString(y)
            )
        ).value
        self.assertEqual(res, x + y)

    @hypothesis.given(st.integers())
    def test_cast_bool_ite(self, x):
        # note this is a runtime error, just like it would be in python!
        source_code = """
def validator(x: int) -> bool:
    if x:
        res = True
    else:
        res = False
    return res
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(x))).value
        self.assertEqual(res, bool(x))

    @hypothesis.given(st.integers())
    def test_cast_bool_ite_expr(self, x):
        # note this is a runtime error, just like it would be in python!
        source_code = """
def validator(x: int) -> bool:
    return True if x else False
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(x))).value
        self.assertEqual(res, bool(x))

    @hypothesis.given(st.integers())
    def test_cast_bool_while(self, x):
        # note this is a runtime error, just like it would be in python!
        source_code = """
def validator(x: int) -> bool:
    res = False
    while x:
        res = True
        x = 0
    return res
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(x))).value
        self.assertEqual(res, bool(x))

    @hypothesis.given(st.integers())
    def test_cast_bool_boolops(self, x):
        # note this is a runtime error, just like it would be in python!
        source_code = """
def validator(x: int) -> bool:
    return x and x or (x or x)
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(x))).value
        self.assertEqual(res, bool(x and x or (x or x)))

    @hypothesis.given(st.integers())
    def test_cast_bool_ite(self, x):
        # note this is a runtime error, just like it would be in python!
        source_code = """
def validator(x: int) -> None:
    assert x
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        try:
            uplc_eval(uplc.Apply(code, uplc.PlutusInteger(x)))
            res = True
        except Exception:
            res = False
        self.assertEqual(res, bool(x))

    @hypothesis.given(a_or_b)
    def test_isinstance_cast_if(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    if isinstance(x, A):
        k = x.foo
    elif isinstance(x, B):
        k = x.bar
    return k
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor()))).value
        self.assertEqual(res, x.foo if isinstance(x, A) else x.bar)

    @hypothesis.given(a_or_b, a_or_b)
    def test_complex_isinstance_cast_if(self, x, y):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B], y: Union[A, B]) -> int:
    if isinstance(x, A) and isinstance(y, B):
        k = x.foo + y.bar
    elif isinstance(x, A) and isinstance(y, A):
        k = x.foo + y.foo
    elif isinstance(x, B) and isinstance(y, A):
        k = x.bar + y.foo
    elif isinstance(x, B) and isinstance(y, B):
        k = x.bar + y.bar
    return k
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(
            uplc.Apply(
                uplc.Apply(code, uplc.data_from_cbor(x.to_cbor())),
                uplc.data_from_cbor(y.to_cbor()),
            )
        ).value
        self.assertEqual(
            res,
            (x.foo if isinstance(x, A) else x.bar)
            + (y.foo if isinstance(y, A) else y.bar),
        )

    @hypothesis.given(a_or_b)
    def test_isinstance_cast_ifexpr(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    k = x.foo if isinstance(x, A) else x.bar if isinstance(x, B) else 0
    return k
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor()))).value
        self.assertEqual(res, x.foo if isinstance(x, A) else x.bar)

    @hypothesis.given(a_or_b)
    def test_isinstance_cast_while(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    foo = 0
    while isinstance(x, B) and foo != 1:
        foo = x.bar
        foo = 1
    return foo
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor()))).value
        self.assertEqual(res, 1 if isinstance(x, B) else 0)

    @hypothesis.given(a_or_b)
    def test_isinstance_cast_random(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> bool:
    return isinstance(x, A)
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor()))).value
        self.assertEqual(res, isinstance(x, A))

    @hypothesis.given(a_or_b, st.integers())
    def test_isinstance_cast_shortcut_and(self, x, y):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B], y: int) -> bool:
    return isinstance(x, A) and x.foo == y or isinstance(x, B) and x.bar == y
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(
            uplc.Apply(
                uplc.Apply(code, uplc.data_from_cbor(x.to_cbor())),
                uplc.PlutusInteger(y),
            )
        ).value
        self.assertEqual(
            res, isinstance(x, A) and x.foo == y or isinstance(x, B) and x.bar == y
        )

    @hypothesis.given(a_or_b)
    def test_isinstance_cast_assert(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    assert isinstance(x, B), "Wrong type"
    return x.bar
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        try:
            res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor()))).value
        except:
            res = None
        self.assertEqual(res, x.bar if isinstance(x, B) else None)

    @unittest.expectedFailure
    def test_isinstance_cast_assert_if(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    if True:
        assert isinstance(x, B), "Wrong type"
    return x.bar
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    @hypothesis.given(a_or_b)
    def test_isinstance_cast_complex_or(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int
    
@dataclass()
class C(PlutusData):
    CONSTR_ID = 2
    foo: int

def validator(x: Union[A, B, C]) -> int:
    if isinstance(x, A) or isinstance(x, C):
        res = x.foo
    else:
        res = 100
    return res
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor()))).value
        self.assertEqual(res, x.foo if isinstance(x, A) else 100)

    @unittest.expectedFailure
    def test_isinstance_cast_complex_or_sameconstr(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

@dataclass()
class C(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[A, B]) -> int:
    if isinstance(x, A) or isinstance(x, C):
        res = x.foo
    else:
        res = 100
    return res
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        print("Union of same constructor id was allowed, should be disallowed")

    @hypothesis.given(a_or_b)
    def test_isinstance_cast_complex_not(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int
    
def validator(x: Union[A, B]) -> int:
    if not isinstance(x, B):
        res = x.foo
    else:
        res = 100
    return res
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor()))).value
        self.assertEqual(res, x.foo if not isinstance(x, B) else 100)

    @hypothesis.given(a_or_b)
    def test_isinstance_cast_complex_ifelse(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    if isinstance(x, A):
        res = x.foo
    else:
        res = x.bar
    return res
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor()))).value
        self.assertEqual(res, x.foo if isinstance(x, A) else x.bar)

    @unittest.expectedFailure
    def test_isinstance_cast_complex_or_else(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    foo = 0
    if isinstance(x, B) or foo == 0:
        foo = x.bar
    else:
        foo = x.foo
    return foo
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    @unittest.expectedFailure
    def test_isinstance_cast_complex_and_else(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    foo = 0
    if isinstance(x, B) and foo == 0:
        foo = x.bar
    else:
        foo = x.foo
    return foo
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    @hypothesis.given(a_or_b, st.integers())
    def test_isinstance_cast_shortcut_or(self, x, y):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B], y: int) -> bool:
    return (isinstance(x, A) or x.bar == y) and (isinstance(x, B) or x.foo == y)
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(
            uplc.Apply(
                uplc.Apply(code, uplc.data_from_cbor(x.to_cbor())),
                uplc.PlutusInteger(y),
            )
        ).value
        self.assertEqual(
            res, (isinstance(x, A) or x.bar == y) and (isinstance(x, B) or x.foo == y)
        )

    @hypothesis.given(a_or_b)
    def test_retype_if(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> Union[A, B]:
    if isinstance(x, A):
        k = B(x.foo, 1)
    else:
        k = A(x.bar)
    return k
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc.plutus_cbor_dumps(
            uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor())))
        )
        self.assertEqual(res, (B(x.foo, 1) if isinstance(x, A) else A(x.bar)).to_cbor())

    @unittest.expectedFailure
    def test_if_no_retype_no_plutusdata(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]):
    if isinstance(x, A):
        k = B(x.foo, 1)
    else:
        k = "hello"
    return k
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    @unittest.expectedFailure
    def test_while_no_retype_no_plutusdata(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]):
    while isinstance(x, A):
        k = B(x.foo, 1)
    else:
        k = "hello"
    return k
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    @hypothesis.given(a_or_b)
    def test_retype_while(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    while isinstance(x, A):
        x = B(x.foo, 1)
    return x.foobar
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.data_from_cbor(x.to_cbor())))
        self.assertEqual(res.value, x.foo if isinstance(x, A) else x.foobar)

    @unittest.expectedFailure
    def test_retype_if_branch_correct(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    if False:
        x = B(0, 1)
    return x.foobar
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    @unittest.expectedFailure
    def test_retype_while_branch_correct(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: Union[A, B]) -> int:
    while False:
        x = B(0, 1)
    return x.foobar
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()

    def test_retype(self):
        source_code = """
def validator(x: int) -> str:
    x = "hello"
    return x
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(1)))
        self.assertEqual(res.value, b"hello")

    def test_retype_if_primitives(self):
        source_code = """
def validator(x: int) -> str:
    if True:
        x = "hello"
    else:
        x = "hi"
    return x
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(1)))
        self.assertEqual(res.value, b"hello")

    @unittest.expectedFailure
    def test_in_list(self):
        source_code = """
from opshin.prelude import *

def validator(
    d: Nothing,
    r: Nothing,
    context: ScriptContext,
):
    assert context.purpose in context.tx_info.signatories
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
