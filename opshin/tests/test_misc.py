import unittest

import frozendict
from hypothesis import given
from hypothesis import strategies as st
from parameterized import parameterized
from uplc import ast as uplc, eval as uplc_eval

from .. import compiler, prelude


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


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
        self.assertEqual(ret, uplc.BuiltinUnit())

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
            ret = uplc_eval(f)
            failed = False
        except Exception as e:
            failed = True
        self.assertTrue(failed, "Machine did validate the content")

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
        self.assertEqual(ret, uplc.BuiltinUnit())

    def test_gift_contract_fail(self):
        input_file = "examples/smart_contracts/gift.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
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
            failed = False
        except Exception as e:
            failed = True
        self.assertTrue(failed, "Machine did validate the content")

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

    def test_dict_datum(self):
        input_file = "examples/dict_datum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ast = compiler.parse(source_code)
        code = compiler.compile(ast)
        code = code.compile()
        f = code.term
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            # required sig missing int this script context
            for d in [
                uplc.PlutusConstr(
                    0,
                    [
                        uplc.PlutusMap(
                            frozendict.frozendict(
                                {
                                    uplc.PlutusConstr(
                                        0, [uplc.PlutusByteString(b"\x01")]
                                    ): 2
                                }
                            )
                        )
                    ],
                ),
            ]:
                f = uplc.Apply(f, d)
            ret = uplc_eval(f)
            failed = False
        except Exception as e:
            failed = True
        self.assertTrue(failed, "Machine did validate the content")

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
        self.assertEqual(ret, [1, 2, 3, 4, 5], "Machine did validate the content")

    def test_redefine_constr(self):
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
        self.assertEqual(ret, bytes([2, 3]), "Machine did validate the content")

    def test_wrap_into_generic_data(self):
        # this tests that errors that are caused by assignments are actually triggered at the time of assigning
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
            uplc.data_from_cbor(
                prelude.SomeOutputDatum(b"a").to_cbor(encoding="bytes")
            ),
            "Machine did validate the content",
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

    def test_union_type_attr_access_all_records(self):
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
        code = compiler.compile(ast)

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
        code = compiler.compile(ast)

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

    @unittest.expectedFailure
    def test_typecast_int_anything(self):
        # this should not compile, we can not upcast with this notation
        # up to discussion whether this should be allowed, but i.g. it should never be necessary or useful
        source_code = """
def validator(x: int) -> Anything:
    b: Anything = x
    return x
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

def validator(x: None) -> None:
    b = a
    if False:
        b()
"""
        ast = compiler.parse(source_code)
        code = compiler.compile(ast).compile()
        res = uplc_eval(uplc.Apply(code, uplc.PlutusInteger(0)))

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
