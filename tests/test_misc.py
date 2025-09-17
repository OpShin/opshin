import os

import sys

import subprocess

import tempfile

import unittest

import frozendict
import frozenlist2
import hypothesis
import pytest
from hypothesis import given
from hypothesis import strategies as st
from parameterized import parameterized

from uplc import ast as uplc

from . import PLUTUS_VM_PROFILE
from opshin import prelude, builder, Purpose, PlutusContract, CompilerError
from .utils import eval_uplc_value, Unit, eval_uplc, eval_uplc_raw, a_or_b, A, B
from opshin.bridge import wraps_builtin
from opshin.compiler_config import OPT_O2_CONFIG, DEFAULT_CONFIG

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)

# these imports are required to eval the result of script context dumps
from opshin.ledger.api_v2 import *

DEFAULT_CONFIG_FORCE_THREE_PARAMS = DEFAULT_CONFIG.update(force_three_params=True)

ALL_EXAMPLES = [
    os.path.join(root, f)
    for root, dirs, files in os.walk("examples")
    for f in files
    if f.endswith(".py") and not f.startswith("broken") and not f.startswith("extract")
]


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


some_output = st.sampled_from([SomeOutputDatum(b"0"), SomeOutputDatumHash(b"1")])


class MiscTest(unittest.TestCase):
    def test_assert_sum_contract_succeed(self):
        input_file = "examples/smart_contracts/assert_sum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc(
            source_code,
            20,
            22,
            uplc.data_from_cbor(
                bytes.fromhex(
                    # TODO need new script context
                    "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87980d87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820746957f0eb57f2b11119684e611a98f373afea93473fefbb7632d579af2f6259ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff"
                )
            ),
            config=DEFAULT_CONFIG.update(OPT_O2_CONFIG),
        )
        self.assertEqual(ret, uplc.PlutusConstr(0, []))

    @unittest.expectedFailure
    def test_assert_sum_contract_fail(self):
        input_file = "examples/smart_contracts/assert_sum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc(source_code, 0, 22, Unit())

    @given(
        a=st.integers(min_value=-10, max_value=10),
        b=st.integers(min_value=0, max_value=10),
    )
    def test_mult_for(self, a: int, b: int):
        input_file = "examples/mult_for.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, a, b)
        self.assertEqual(ret, a * b)

    @given(
        a=st.integers(min_value=-10, max_value=10),
        b=st.integers(min_value=0, max_value=10),
    )
    def test_mult_for(self, a: int, b: int):
        input_file = "examples/mult_for.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, a, b)
        self.assertEqual(ret, a * b)

    @given(
        a=st.integers(),
        b=st.integers(),
    )
    def test_sum(self, a: int, b: int):
        input_file = "examples/sum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, a, b)
        self.assertEqual(ret, a + b)

    def test_complex_datum_correct_vals(self):
        input_file = "examples/complex_datum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(
            source_code,
            uplc.data_from_cbor(
                bytes.fromhex(
                    "d8799fd8799fd8799f581c81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acfffd8799fd8799fd8799f581c145db8343296bd214dde862a64d700c29ed8a71d58bcf865659f5463ffffffffd8799fd8799f581c81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acfffd8799fd8799fd8799f581c145db8343296bd214dde862a64d700c29ed8a71d58bcf865659f5463ffffffffd87a80d8799f1a38220b0bff1a001e84801a001e8480582051176daeee7f2ce62963c50a16f641951e21b8522da262980d4dd361a9bf331b4e4d7565736c69537761705f414d4dff"
                )
            ),
        )
        self.assertEqual(
            bytes.fromhex("81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acf"),
            ret,
        )

    def test_hello_world(self):
        input_file = "examples/hello_world.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc(source_code, Unit())

    def test_list_datum_correct_vals(self):
        input_file = "examples/list_datum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(
            source_code, uplc.data_from_cbor(bytes.fromhex("d8799f9f41014102ffff"))
        )
        self.assertEqual(
            1,
            ret,
        )

    def test_showcase(self):
        input_file = "examples/showcase.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, 1)
        self.assertEqual(
            42,
            ret,
        )

    @given(n=st.integers(min_value=0, max_value=5))
    def test_fib_iter(self, n):
        input_file = "examples/fib_iter.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, n)
        self.assertEqual(
            fib(n),
            ret,
        )

    @given(n=st.integers(min_value=0, max_value=5))
    def test_fib_rec(self, n):
        input_file = "examples/fib_rec.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, n)
        self.assertEqual(
            fib(n),
            ret,
        )

    def test_gift_contract_succeed(self):
        input_file = "examples/smart_contracts/gift.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc(
            source_code,
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
        )
        self.assertEqual(ret, uplc.PlutusConstr(0, []))

    @unittest.expectedFailure
    def test_gift_contract_fail(self):
        input_file = "examples/smart_contracts/gift.py"
        with open(input_file) as fp:
            source_code = fp.read()
        # required sig missing int this script context
        ret = eval_uplc(
            source_code,
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
        )

    def test_recursion_simple(self):
        source_code = """
def validator(_: None) -> int:
    def a(n: int) -> int:
      if n == 0:
        res = 0
      else:
        res = a(n-1)
      return res
    return a(1)
        """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(0, ret)

    @unittest.expectedFailure
    def test_recursion_illegal(self):
        # this is now an illegal retyping because read variables dont match
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
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(100, ret)

    def test_recursion_legal(self):
        source_code = """
def validator(_: None) -> int:
    def a(n: int) -> int:
      if n == 0:
        res = 0
      else:
        res = a(n-1)
      return res
    b = a
    def a(n: int) -> int:
      a
      if 1 == n:
        pass
      return 100
    return b(1)
        """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(100, ret)

    def test_mutual_recursion_even_odd(self):
        source_code = """
def even(n: int) -> bool:
    if n == 0:
        return True
    else:
        return odd(n - 1)
        
def odd(n: int) -> bool:
    if n == 0:
        return False
    else:
        return even(n - 1)

def validator(n: int) -> int:
    if even(n):
        return 1
    else:
        return 0
        """
        # Test with even number
        ret = eval_uplc_value(source_code, 4)
        self.assertEqual(1, ret)
        # Test with odd number  
        ret = eval_uplc_value(source_code, 3)
        self.assertEqual(0, ret)

    def test_mutual_recursion_three_way(self):
        source_code = """
def a(n: int) -> int:
    if n <= 0:
        return 1
    else:
        return b(n - 1)

def b(n: int) -> int:
    if n <= 0:
        return 2
    else:
        return c(n - 1)

def c(n: int) -> int:
    if n <= 0:
        return 3
    else:
        return a(n - 1)

def validator(n: int) -> int:
    return a(n)
        """
        # Test different values to verify the three-way recursion pattern
        ret = eval_uplc_value(source_code, 0)
        self.assertEqual(1, ret)  # a(0) = 1
        ret = eval_uplc_value(source_code, 1)
        self.assertEqual(2, ret)  # a(1) = b(0) = 2
        ret = eval_uplc_value(source_code, 2)
        self.assertEqual(3, ret)  # a(2) = b(1) = c(0) = 3
        ret = eval_uplc_value(source_code, 3)
        self.assertEqual(1, ret)  # a(3) = b(2) = c(1) = a(0) = 1

    @unittest.expectedFailure
    def test_uninitialized_access(self):
        source_code = """
def validator(_: None) -> int:
    b = 1
    def a(n: int) -> int:
      b += 1
      if b == 2:
        return 0
      else:
        return a(n-1)
    return a(1)
        """
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_illegal_bind(self):
        source_code = """
def validator(_: None) -> int:
    b = 1
    def a(n: int) -> int:
      if n == 0:
        return 100
      if b == 2:
        return 0
      b = 2
      return a(n-1)
    return a(2)
        """
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_type_reassignment_function_bound(self):
        # changing the type of a variable should be disallowed if the variable is bound by a function
        # it can be ok if the types can be merged (resulting in union type inside the function) but
        # generally should be disallowed
        source_code = """
def validator(_: None) -> int:
    b = 1
    def a(n: int) -> int:
      return b
    b = b''
    return a(1)
        """
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_illegal_function_retype(self):
        source_code = """
def validator(_: None) -> int:
    def a(n: int) -> int:
      if n == 0:
        res = 0
      else:
        res = a(n-1)
      return res
    b = a
    def a() -> int:
      return 100
    return b(1)
        """
        builder._compile(source_code)

    def test_datum_cast(self):
        input_file = "examples/datum_cast.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(
            source_code,
            uplc.data_from_cbor(
                bytes.fromhex(
                    "d8799fd8799fd8799f581c81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acfffd8799fd8799fd8799f581c145db8343296bd214dde862a64d700c29ed8a71d58bcf865659f5463ffffffffd8799fd8799f581c81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acfffd8799fd8799fd8799f581c145db8343296bd214dde862a64d700c29ed8a71d58bcf865659f5463ffffffffd87a80d8799f1a38220b0bff1a001e84801a001e8480582051176daeee7f2ce62963c50a16f641951e21b8522da262980d4dd361a9bf331b4e4d7565736c69537761705f414d4dff"
                )
            ),
            uplc.PlutusByteString(b"test"),
        )
        self.assertEqual(
            bytes.fromhex("81aab0790f33d26bad68a6a13ae98562aa1366da48cdce20dec21acf")
            + b"test",
            ret,
        )

    def test_wrapping_contract_compile(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/wrapped_token.py"
        with open(input_file) as fp:
            source_code = fp.read()
        builder._compile(source_code, config=DEFAULT_CONFIG_FORCE_THREE_PARAMS)

    def test_dual_use_compile(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/dual_use.py"
        with open(input_file) as fp:
            source_code = fp.read()
        builder._compile(source_code, config=DEFAULT_CONFIG_FORCE_THREE_PARAMS)

    def test_marketplace_compile(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/marketplace.py"
        with open(input_file) as fp:
            source_code = fp.read()
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_marketplace_compile_fail(self):
        input_file = "examples/smart_contracts/marketplace.py"
        with open(input_file) as fp:
            source_code = fp.read()
        builder._compile(source_code, config=DEFAULT_CONFIG_FORCE_THREE_PARAMS)

    def test_parameterized_compile(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/parameterized.py"
        with open(input_file) as fp:
            source_code = fp.read()
        builder._compile(source_code, config=DEFAULT_CONFIG_FORCE_THREE_PARAMS)

    def test_dict_datum(self):
        input_file = "examples/dict_datum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        d = uplc.PlutusConstr(
            0,
            [
                uplc.PlutusMap(
                    frozendict.frozendict(
                        {
                            uplc.PlutusConstr(
                                0,
                                frozenlist2.frozenlist(
                                    [uplc.PlutusByteString(b"\x01")]
                                ),
                            ): uplc.PlutusInteger(2)
                        }
                    )
                )
            ],
        )
        ret = eval_uplc(source_code, d)
        self.assertTrue(bool(ret))

    def test_dict_datum_wrong(self):
        input_file = "examples/dict_datum.py"
        with open(input_file) as fp:
            source_code = fp.read()
        d = uplc.PlutusConstr(
            0,
            [
                uplc.PlutusMap(
                    frozendict.frozendict(
                        {
                            uplc.PlutusConstr(
                                0,
                                frozenlist2.frozenlist(
                                    [uplc.PlutusByteString(b"\x02")]
                                ),
                            ): uplc.PlutusInteger(2)
                        }
                    )
                )
            ],
        )
        ret = eval_uplc_value(source_code, d)
        self.assertFalse(bool(ret))

    def test_removedeadvar_noissue(self):
        source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    b = 4
    a = b
    return True
        """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(ret, True)

    def test_removedeadvar_noissue2(self):
        source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    def foo(x: Token) -> bool:
        b = 4
        a = b
        return True
    return foo(x)
        """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(ret, True)

    def test_removedeadvar_noissue3(self):
        source_code = """
from opshin.prelude import *

def foo(x: Token) -> bool:
    b = 4
    a = b
    return True

def validator(x: Token) -> bool:
    return foo(x)
        """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(ret, True)

    @unittest.expectedFailure
    def test_overopt_removedeadvar(self):
        source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    a = x.policy_id
    return True
        """
        ret = eval_uplc(source_code, Unit())

    @unittest.expectedFailure
    def test_opt_shared_var(self):
        source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    if False:
        y = x
    else:
        a = y
    return True
        """
        ret = eval_uplc(source_code, Unit())

    def test_list_expr(self):
        # this tests that the list expression is evaluated correctly
        source_code = """
from typing import Dict, List, Union

def validator(x: None) -> List[int]:
    return [1, 2, 3, 4, 5]
        """
        ret = eval_uplc_value(source_code, Unit())
        ret = [x.value for x in ret]
        self.assertEqual(ret, [1, 2, 3, 4, 5], "List expression incorrectly compiled")

    def test_list_expr_not_const(self):
        # this tests that the list expression is evaluated correctly (for non-constant expressions)
        source_code = """
from typing import Dict, List, Union

def validator(x: int) -> List[int]:
    return [x, x+1, x+2, x+3, x+4]
        """
        ret = eval_uplc_value(source_code, 1)
        ret = [x.value for x in ret]
        self.assertEqual(ret, [1, 2, 3, 4, 5], "List expression incorrectly compiled")

    def test_dict_expr_not_const(self):
        # this tests that the list expression is evaluated correctly (for non-constant expressions)
        source_code = """
from typing import Dict, List, Union

def validator(x: int) -> Dict[int, bytes]:
    return {x: b"a", x+1: b"b"}
        """
        ret = eval_uplc_value(source_code, 1)
        ret = {x.value: y.value for x, y in ret.items()}
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
        ret = eval_uplc_value(source_code, Unit())
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
        ret = eval_uplc_value(source_code, int(x))
        self.assertEqual(ret, int(x), "Re-assignment of class constr failed")

    def test_wrap_into_generic_data(self):
        # this tests data is wrapped into Anything if a function accepts Anything
        source_code = """
from opshin.prelude import *
def validator(_: None) -> SomeOutputDatum:
    return SomeOutputDatum(b"a")
        """
        ret = eval_uplc(source_code, Unit())
        self.assertEqual(
            ret,
            uplc.data_from_cbor(prelude.SomeOutputDatum(b"a").to_cbor()),
            "Wrapping to generic data failed",
        )

    def test_list_comprehension_even(self):
        input_file = "examples/list_comprehensions.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, 8, 1)
        ret = [x.value for x in ret]
        self.assertEqual(
            ret,
            [x * x for x in range(8) if x % 2 == 0],
            "List comprehension with filter incorrectly evaluated",
        )

    def test_list_comprehension_all(self):
        input_file = "examples/list_comprehensions.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, 8, 0)
        ret = [x.value for x in ret]
        self.assertEqual(
            ret,
            [x * x for x in range(8)],
            "List comprehension incorrectly evaluated",
        )

    def test_dict_comprehension_even(self):
        input_file = "examples/dict_comprehensions.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, 8, 1)
        ret = {x.value: y.value for x, y in ret.items()}
        self.assertEqual(
            ret,
            {x: x * x for x in range(8) if x % 2 == 0},
            "Dict comprehension incorrectly evaluated",
        )

    def test_dict_comprehension_all(self):
        input_file = "examples/dict_comprehensions.py"
        with open(input_file) as fp:
            source_code = fp.read()
        ret = eval_uplc_value(source_code, 8, 0)
        ret = {x.value: y.value for x, y in ret.items()}
        self.assertEqual(
            ret,
            {x: x * x for x in range(8)},
            "Dict comprehension incorrectly evaluated",
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

        @dataclass()
        class A(PlutusData):
            CONSTR_ID = 0
            foo: SomeOutputDatumHash

        @dataclass()
        class B(PlutusData):
            CONSTR_ID = 1
            foo: SomeOutputDatum

        x = A(x) if isinstance(x, SomeOutputDatumHash) else B(x)

        ret = eval_uplc(source_code, x)
        self.assertEqual(ret, uplc.data_from_cbor(x.foo.to_cbor()))

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
            else B(x) if y == 1 else C(0, x) if y == 2 else D(0, 0, x)
        )

        ret = eval_uplc(source_code, x)
        self.assertEqual(ret, uplc.data_from_cbor(x.foo.to_cbor()))

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
        eval_uplc(source_code, Unit())

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
        eval_uplc(source_code, Unit())

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
        ret = eval_uplc_value(
            source_code, uplc.PlutusConstr(0, [uplc.PlutusInteger(1)])
        )
        self.assertEqual(ret, 1)

    def test_union_type_attr_anytype(self):
        source_code = """
from opshin.prelude import *

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: bytes

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foo: int

def validator(x: Union[A, B]) -> Anything:
    return x.foo
"""
        ret = eval_uplc_value(
            source_code, uplc.PlutusConstr(0, [uplc.PlutusByteString(b"")])
        )
        self.assertEqual(ret, b"")

    def test_typecast_anything_int(self):
        source_code = """
def validator(x: Anything) -> int:
    b: int = x
    return b
"""
        ret = eval_uplc_value(source_code, 0)
        self.assertEqual(ret, 0)

    def test_typecast_int_anything(self):
        # this should compile, it happens implicitly anyways when calling a function with Any parameters
        source_code = """
def validator(x: int) -> Anything:
    b: Anything = x
    return b
"""
        ret = eval_uplc_value(source_code, 0)
        self.assertEqual(ret, 0)

    def test_typecast_int_anything_int(self):
        source_code = """
def validator(x: int) -> Anything:
    b: Anything = x
    c: int = b
    return c + 1
"""
        ret = eval_uplc_value(source_code, 0)
        self.assertEqual(ret, 1)

    def test_typecast_anything_int_anything(self):
        source_code = """
def validator(x: Anything) -> Anything:
    b: int = x
    c: Anything = b + 1
    return c
"""
        ret = eval_uplc_value(source_code, 0)
        self.assertEqual(ret, 1)

    @unittest.expectedFailure
    def test_typecast_int_str(self):
        # this should not compile, the two types are unrelated and there is no meaningful way to cast them either direction
        source_code = """
def validator(x: int) -> str:
    b: str = x
    return b
"""
        builder._compile(source_code)

    def test_typecast_int_int(self):
        source_code = """
def validator(x: int) -> int:
    b: int = x
    return b
"""
        ret = eval_uplc_value(source_code, 0)
        self.assertEqual(ret, 0)

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
        ret = eval_uplc_value(source_code, 0)
        self.assertEqual(ret, 2, "Invalid return value")

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
        ret = eval_uplc_value(source_code, 0)

    def test_zero_ary_method(self):
        source_code = """
def validator(x: None) -> None:
    b = b"\\xFF".decode
    if False:
        b()
"""
        eval_uplc(source_code, 0)

    @unittest.expectedFailure
    def test_zero_ary_method_exec(self):
        source_code = """
def validator(x: None) -> None:
    b = b"\\xFF".decode
    if True:
        b()
"""
        eval_uplc(source_code, 0)

    def test_zero_ary_method_exec_suc(self):
        source_code = """
def validator(x: None) -> str:
    b = b"\\x32".decode
    return b()
"""
        res = eval_uplc_value(source_code, 0)
        self.assertEqual(res, b"\x32")

    def test_return_anything(self):
        source_code = """
from opshin.prelude import *

def validator() -> Anything:
    return b""
"""
        res = eval_uplc(source_code, 0)
        self.assertEqual(res, uplc.PlutusByteString(b""))

    def test_no_return_annotation(self):
        source_code = """
from opshin.prelude import *

def validator():
    return b""
"""
        res = eval_uplc(source_code, 0)
        self.assertEqual(res, uplc.PlutusByteString(b""))

    def test_no_parameter_annotation(self):
        source_code = """
from opshin.prelude import *

def validator(a) -> bytes:
    b: bytes = a
    return b
"""
        res = eval_uplc(source_code, b"")
        self.assertEqual(res, uplc.PlutusByteString(b""))

    def test_no_return_annotation_no_return(self):
        source_code = """
from opshin.prelude import *

def validator(a):
    pass
"""
        res = eval_uplc(source_code, 0)
        self.assertEqual(res, uplc.PlutusConstr(0, []))

    @unittest.expectedFailure
    def test_opt_unsafe_cast(self):
        # test that unsafe casts are not optimized away
        source_code = """
from opshin.prelude import *
def validator(x: Token) -> bool:
    b: Anything = x
    a: int = b
    return True
        """
        ret = eval_uplc(source_code, Unit())

    def test_reassign_builtin(self):
        source_code = """
b = int
def validator(_: None) -> int:
    def int(a) -> b:
        return 2
    return int(5)
"""
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, 2)

    @unittest.expectedFailure
    def test_reassign_builtin_invalid_type(self):
        source_code = """
def validator(_: None) -> int:
    def int(a) -> int:
        return 2
    return int(5)
"""
        builder._compile(source_code)

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
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, 2)

    def test_outer_state_change_functions(self):
        source_code = """
a = 2
def b() -> int:
    return a
a = 3

def validator(_: None) -> int:
    return b()
"""
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, 3)

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
        eval_uplc(source_code, Unit())

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
        eval_uplc(source_code, Unit())

    @unittest.expectedFailure
    def test_access_local_variable_before_assignment(self):
        # note this is a runtime error, just like it would be in python!
        source_code = """
a = "1"
def validator(_: None) -> None:
   print(a)
   a = "2"
"""
        eval_uplc(source_code, Unit())

    def test_warn_bytestring(self):
        source_code = """
b = b"0011ff"
def validator(_: None) -> None:
    pass
"""
        eval_uplc(source_code, Unit())

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
        source_code = """
from opshin.prelude import *

def validator(c: ScriptContext) -> str:
    return f"{c}"
        """
        res = eval_uplc_value(source_code, context)
        # should not raise
        from pycardano import RawPlutusData  # noqa: F401
        from cbor2 import CBORTag  # noqa: F401

        eval(res)

    @hypothesis.given(st.binary(), st.binary())
    def test_uplc_builtin(self, x, y):
        source_code = """
from opshin.std.builtins import *
def validator(x: bytes, y: bytes) -> bytes:
    return append_byte_string(x, y)
"""
        res = eval_uplc_value(source_code, x, y)
        self.assertEqual(res, x + y)

    def test_trace_order(self):
        # TODO can become a proper test once uplc is upgraded to >=1.0.0
        source_code = """
from opshin.std.builtins import *
def validator() -> None:
    print("test")
    print("hi")
    print("there")
    return None
"""
        eval_uplc(source_code, PlutusData())

    def test_print_empty(self):
        # TODO can become a proper test once uplc is upgraded to >=1.0.0
        source_code = """
from opshin.std.builtins import *
def validator() -> None:
    print()
    print()
    print()
    print()
    print()
    print()
    return None
"""
        eval_uplc(source_code, PlutusData())

    @hypothesis.given(st.integers())
    def test_cast_bool_ite(self, x):
        source_code = """
def validator(x: int) -> bool:
    if x:
        res = True
    else:
        res = False
    return res
"""
        res = eval_uplc_value(source_code, x)
        self.assertEqual(res, bool(x))

    @hypothesis.given(st.integers())
    def test_cast_bool_ite_expr(self, x):
        source_code = """
def validator(x: int) -> bool:
    return True if x else False
"""
        res = eval_uplc_value(source_code, x)
        self.assertEqual(bool(res), bool(x))

    @hypothesis.given(st.integers())
    def test_cast_bool_while(self, x):
        source_code = """
def validator(x: int) -> bool:
    res = False
    while x:
        res = True
        x = 0
    return res
"""
        res = eval_uplc_value(source_code, x)
        self.assertEqual(bool(res), bool(x))

    @hypothesis.given(st.integers())
    def test_cast_bool_boolops(self, x):
        source_code = """
def validator(x: int) -> bool:
    return x and x or (x or x)
"""
        res = eval_uplc_value(source_code, x)
        self.assertEqual(bool(res), bool(x and x or (x or x)))

    @hypothesis.given(st.integers())
    def test_cast_bool_ite(self, x):
        source_code = """
def validator(x: int) -> None:
    assert x
"""
        try:
            eval_uplc(source_code, x)
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
        res = eval_uplc_value(source_code, x)
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
        res = eval_uplc_value(source_code, x, y)
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
        res = eval_uplc_value(source_code, x)
        self.assertEqual(res, x.foo if isinstance(x, A) else x.bar)

    def test_ifexpr_check_same_type(self):
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
    k = x.foo if isinstance(x, A) else str(x) if isinstance(x, B) else 0
    return k
"""
        with self.assertRaises(CompilerError) as e:
            builder._compile(source_code)
        self.assertIn("Branches of if-expression", str(e.exception))

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
        res = eval_uplc_value(source_code, x)
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
        res = eval_uplc_value(source_code, x)
        self.assertEqual(res, isinstance(x, A))

    @hypothesis.given(a_or_b, st.integers())
    @hypothesis.example(A(0), 0)
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
        res = eval_uplc_value(source_code, x, y)
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
        try:
            res = eval_uplc_value(source_code, x)
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
        builder._compile(source_code)

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
        res = eval_uplc_value(source_code, x)
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
        builder._compile(source_code)
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
        res = eval_uplc_value(source_code, x)
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
        res = eval_uplc_value(source_code, x)
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
        builder._compile(source_code)

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
        builder._compile(source_code)

    def test_isinstance_cast_complex_and(self):
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
    return foo
"""
        builder._compile(source_code)

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
        res = eval_uplc_value(source_code, x, y)
        self.assertEqual(
            res, (isinstance(x, A) or x.bar == y) and (isinstance(x, B) or x.foo == y)
        )

    @hypothesis.given(a_or_b)
    def test_uniontype_if(self, x):
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
        res = uplc.plutus_cbor_dumps(eval_uplc(source_code, x))
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
        builder._compile(source_code)

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
        builder._compile(source_code)

    @unittest.expectedFailure
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
        res = eval_uplc_value(source_code, x)
        self.assertEqual(res, x.foo if isinstance(x, A) else x.foobar)

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
        builder._compile(source_code)

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
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_retype_while_wrong_after_iter(self):
        source_code = """
def validator(x: int) -> bytes:
    while True:
        x += 1
        x = b''
    return x
"""
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_retype(self):
        source_code = """
def validator(x: int) -> str:
    x = "hello"
    return x
"""
        res = eval_uplc_value(source_code, 1)
        self.assertEqual(res, b"hello")

    @unittest.expectedFailure
    def test_retype_if_primitives(self):
        source_code = """
def validator(x: int) -> str:
    if True:
        x = "hello"
    else:
        x = "hi"
    return x
"""
        res = eval_uplc_value(source_code, 1)
        self.assertEqual(res, b"hello")

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
        builder._compile(source_code)

    def test_bytearray_alternative(self):
        source_code = """
def validator(
    d: bytearray,
) -> bytes:
    return d
"""
        eval_uplc(source_code, bytearray(b"hello"))

    # TODO enable when pycardano version is fixed s.t. import of ByteString works
    @unittest.expectedFailure
    def test_ByteString_alternative(self):
        source_code = """
def validator(
    d: ByteString,
) -> bytes:
    return d
"""
        eval_uplc(source_code, bytearray(b"hello"))

    @hypothesis.given(
        st.lists(
            st.tuples(st.booleans(), st.sampled_from(["and", "or"])),
            max_size=10,
            min_size=2,
        )
    )
    def test_boolop_chaining(self, xs):
        param_string = ",".join(f"i{k}: bool" for k, _ in enumerate(xs))
        comp_string = "i0"
        eval_string = f"{xs[0][0]}"
        for k, (x, c) in enumerate(xs[1:], start=1):
            comp_string += f" {c} i{k}"
            eval_string += f" {c} {x}"
        source_code = f"""
def validator({param_string}) -> bool:
    return {comp_string}
"""
        res = eval_uplc_value(source_code, *[x[0] for x in xs])
        self.assertEqual(bool(res), eval(eval_string))

    def test_wrapping_contract_apply(self):
        # TODO devise tests for this
        input_file = "examples/smart_contracts/wrapped_token.py"
        contract = builder.build(input_file, config=DEFAULT_CONFIG_FORCE_THREE_PARAMS)
        artifacts = PlutusContract(
            contract,
            datum_type=("datum", prelude.Nothing),
            redeemer_type=("redeemer", prelude.Nothing),
            parameter_types=[
                ("token_policy_id", bytes),
                ("token_name", bytes),
                ("wrapping_factor", int),
            ],
            purpose=[Purpose.spending, Purpose.minting],
        )
        applied = artifacts.apply_parameter(b"", b"")
        assert len(applied.parameter_types) == 1
        assert applied.parameter_types[0][0] == "wrapping_factor"
        assert applied.datum_type == ("datum", prelude.Nothing)

    def test_wrapping_contract_dump_load(self):
        input_file = "examples/smart_contracts/wrapped_token.py"
        contract = builder.build(input_file, config=DEFAULT_CONFIG_FORCE_THREE_PARAMS)
        artifacts = PlutusContract(
            contract,
            datum_type=("datum", prelude.Nothing),
            redeemer_type=("redeemer", prelude.ScriptContext),
            parameter_types=[
                ("token_policy_id", bytes),
                ("token_name", bytes),
                ("wrapping_factor", int),
            ],
            purpose=[Purpose.spending, Purpose.minting],
            description="Wrapped token contract",
            license="MIT",
        )
        target_dir = tempfile.TemporaryDirectory()
        artifacts.dump(target_dir.name)
        loaded = builder.load(target_dir.name)
        assert len(loaded.parameter_types) == len(artifacts.parameter_types)
        assert loaded.datum_type[1].__name__ == artifacts.datum_type[1].__name__
        assert loaded.datum_type[0] == artifacts.datum_type[0]
        assert loaded.datum_type[1].CONSTR_ID == artifacts.datum_type[1].CONSTR_ID
        assert loaded.redeemer_type[1].__name__ == artifacts.redeemer_type[1].__name__
        assert loaded.redeemer_type[0] == artifacts.redeemer_type[0]
        assert loaded.redeemer_type[1].CONSTR_ID == artifacts.redeemer_type[1].CONSTR_ID
        assert loaded.purpose == artifacts.purpose
        assert loaded.description == artifacts.description
        assert loaded.license == artifacts.license
        assert loaded.title == artifacts.title
        assert loaded.version == artifacts.version

    @unittest.expectedFailure
    def test_forbidden_overwrite(self):
        source_code = """
def validator(
    d: int
):
    PlutusData = d
    return d
"""
        builder._compile(source_code)

    @parameterized.expand(ALL_EXAMPLES)
    def test_compilation_deterministic_local(self, input_file):
        with open(input_file) as fp:
            source_code = fp.read()
        code = builder._compile(source_code)
        for i in range(10):
            code_2 = builder._compile(source_code)
            self.assertEqual(code.dumps(), code_2.dumps())

    @parameterized.expand(ALL_EXAMPLES)
    def test_compilation_deterministic_external(self, input_file):
        code = subprocess.run(
            [
                sys.executable,
                "-m",
                "opshin",
                "compile",
                "any",
                input_file,
            ],
            capture_output=True,
        )
        for i in range(10):
            code_2 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "opshin",
                    "compile",
                    "any",
                    input_file,
                ],
                capture_output=True,
            )
            self.assertEqual(code.stdout, code_2.stdout)

    @unittest.expectedFailure
    def test_return_illegal(self):
        # this is now an illegal retyping because read variables dont match
        source_code = """
return 1
def validator(_: None) -> int:
    return 0
        """
        builder._compile(source_code)

    def test_return_in_loop(self):
        source_code = """
def validator(_: None) -> int:
    i = 0
    while i < 10:
        i += 1
        if i == 5:
          return i
    return 0
        """
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, 5, "Invalid return break")

    def test_return_in_for(self):
        source_code = """
def validator(_: None) -> int:
    i = 0
    for i in range(10):
        i += 1
        if i == 5:
          return i
    return 0
        """
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, 5, "Invalid return break")

    def test_return_in_if(self):
        source_code = """
def validator(_: None) -> int:
    i = 0
    if i == 1:
        return 0
    else:
        return 1
        """
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, 1, "Invalid return")

    @unittest.expectedFailure
    def test_return_in_if_same_type(self):
        source_code = """
def validator(_: None) -> str:
    i = 0
    if i == 1:
        return "a"
    else:
        return 1
        """
        builder._compile(source_code)

    def test_isinstance_cast_if2(self):
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

def validator(_: None) -> Union[A, B]:
    x = 0
    if x == 1:
        return A(1)
    else:
        return B(2, 1)
"""
        res = eval_uplc(source_code, Unit())
        self.assertEqual(
            res,
            uplc.PlutusConstr(1, [uplc.PlutusInteger(2), uplc.PlutusInteger(1)]),
            "Invalid return",
        )

    @unittest.expectedFailure
    def test_return_in_if_missing_return(self):
        source_code = """
def validator(_: None) -> str:
    i = 0
    if i == 1:
        return "a"
    else:
        pass
        """
        builder._compile(source_code)

    def test_different_return_types_anything(self):
        source_code = """
from opshin.prelude import *

def validator(a: int) -> Anything:
    if a > 0:
        return b""
    else:
        return 0
"""
        res = eval_uplc(source_code, 1)
        self.assertEqual(res, uplc.PlutusByteString(b""))
        res = eval_uplc(source_code, -1)
        self.assertEqual(res, uplc.PlutusInteger(0))

    @unittest.expectedFailure
    def test_different_return_types_while_loop(self):
        source_code = """
def validator(a: int) -> str:
    while a > 0:
        return b""
    return 0
"""
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_different_return_types_for_loop(self):
        source_code = """
def validator(a: int) -> str:
    for i in range(a):
        return b""
    return 0
"""
        builder._compile(source_code)

    def test_return_else_loop_while(self):
        source_code = """
def validator(a: int) -> int:
    while a > 0:
        a -= 1
    else:
        return 0
"""
        res = eval_uplc_value(source_code, 1)
        self.assertEqual(res, 0, "Invalid return")

    def test_return_else_loop_for(self):
        source_code = """
def validator(a: int) -> int:
    for _ in range(a):
        a -= 1
    else:
        return 0
"""
        res = eval_uplc_value(source_code, 1)
        self.assertEqual(res, 0, "Invalid return")

    def test_empty_list_int(self):
        source_code = """
from typing import Dict, List, Union

def validator(_: None) -> List[int]:
    a: List[int] = []
    return a + [1]
"""
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, [uplc.PlutusInteger(1)])

    def test_empty_list_data(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> List[Token]:
    a: List[Token] = []
    return a + [Token(b"", b"")]
"""
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(
            res,
            [
                uplc.PlutusConstr(
                    0, [uplc.PlutusByteString(b""), uplc.PlutusByteString(b"")]
                )
            ],
        )

    def test_empty_dict_int_int(self):
        source_code = """
from typing import Dict, List, Union

def validator(_: None) -> Dict[int, int]:
    a: Dict[int, int] = {}
    return a
"""
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, {})

    def test_union_subset_call(self):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from dataclasses import dataclass

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    bar: int

@dataclass()
class C(PlutusData):
    CONSTR_ID = 2
    foobar: int

def fun(x: Union[A, B, C]) -> int:
    return 0


def validator(x: Union[A, B]) -> int:
    return fun(x)
        """
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_union_superset_call(self):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from dataclasses import dataclass

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    bar: int

@dataclass()
class C(PlutusData):
    CONSTR_ID = 2
    foobar: int

def fun(x: Union[A, B]) -> int:
    return 0


def validator(x: Union[A, B, C]) -> int:
    return fun(x)
        """
        builder._compile(source_code)

    @unittest.expectedFailure
    def test_merge_function_same_capture_different_type(self):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from dataclasses import dataclass

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    bar: int

def validator(x: bool) -> int:
    if x:
        y = A(0)
        def foo() -> int:
            return y.foo
    else:
        y = B(0)
        def foo() -> int:
            return y.bar
    y = A(0)
    return foo()
        """
        builder._compile(source_code)

    def test_merge_function_same_capture_same_type(self):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from dataclasses import dataclass

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    bar: int

def validator(x: bool) -> int:
    if x:
        y = A(0)
        def foo() -> int:
            print(2)
            return y.foo
    else:
        y = A(0) if x else B(0)
        def foo() -> int:
            print(y)
            return 2
    y = A(0)
    return foo()
        """
        res_true = eval_uplc_value(source_code, 1)
        res_false = eval_uplc_value(source_code, 0)
        self.assertEqual(res_true, 0)
        self.assertEqual(res_false, 2)

    def test_merge_print(self):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from dataclasses import dataclass

def validator(x: bool) -> None:
    if x:
        a = print
    else:
        b = print
        a = b
    return a(x)
        """
        res_true = eval_uplc(source_code, 1)
        res_false = eval_uplc(source_code, 0)

    def test_print_reassign(self):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from dataclasses import dataclass

def validator(x: bool) -> None:
    a = print
    return a(x)
        """
        res_true = eval_uplc(source_code, 1)
        res_false = eval_uplc(source_code, 0)

    def test_str_constr_reassign(self):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from dataclasses import dataclass

def validator(x: bool) -> str:
    a = str
    return a(x)
        """
        res_true = eval_uplc_value(source_code, 1)
        res_false = eval_uplc_value(source_code, 0)

    @unittest.expectedFailure
    def test_class_attribute_access(self):
        source_code = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    a: int
    b: bytes
    d: List[int]

def validator(_: None) -> int:
    return A.CONSTR_ID
    """
        builder._compile(source_code)

    def test_constr_id_access(self):
        source_code = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union

@dataclass
class A(PlutusData):
    CONSTR_ID = 15
    a: int
    b: bytes
    d: List[int]

def validator(_: None) -> int:
    return A(0, b"", [1,2]).CONSTR_ID
    """
        res = eval_uplc_value(source_code, Unit())

        self.assertEqual(15, res, "Invalid constr id")

    def test_id_map_equals_pycardano(self):
        @dataclass
        class A(PlutusData):
            CONSTR_ID = 0
            a: int
            b: bytes
            d: List[int]

        @dataclass
        class C(PlutusData):
            z: Anything

        @dataclass
        class B(PlutusData):
            a: int
            c: A
            d: Dict[bytes, C]
            e: Union[A, C]

        source_code = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union

@dataclass
class Nothing(PlutusData):
    CONSTR_ID = 0
    

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    a: int
    b: bytes
    d: List[int]

@dataclass
class C(PlutusData):
    z: Anything

@dataclass
class B(PlutusData):
    a: int
    c: A
    d: Dict[bytes, C]
    e: Union[A, C]
    
def validator(_: None) -> int:
    return B(1, A(1, b"", [1, 2]), {b"": C(Nothing())}, C(Nothing())).CONSTR_ID
    """
        res = eval_uplc_value(source_code, Unit())

        self.assertEqual(
            B.CONSTR_ID, res, "Invalid constr id generation (does not match pycardano)"
        )

    def test_id_map_equals_pycardano_2(self):
        @dataclass
        class A(PlutusData):
            CONSTR_ID = 0
            a: int
            b: bytes
            d: List[int]

        @dataclass
        class C(PlutusData):
            z: Anything

        @dataclass
        class B(PlutusData):
            a: int
            c: A
            d: Dict[bytes, C]
            e: Union[A, C]

        @dataclass
        class E(PlutusData):
            e: Union[A, Union[B, C]]

        source_code = """
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union

@dataclass
class Nothing(PlutusData):
    CONSTR_ID = 0


@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    a: int
    b: bytes
    d: List[int]

@dataclass
class C(PlutusData):
    z: Anything

@dataclass
class B(PlutusData):
    a: int
    c: A
    d: Dict[bytes, C]
    e: Union[A, C]

@dataclass
class E(PlutusData):
    e: Union[A, Union[B,C]]

def validator(_: None) -> int:
    return E(C(Nothing())).CONSTR_ID
    """
        res = eval_uplc_value(source_code, Unit())

        self.assertEqual(
            E.CONSTR_ID, res, "Invalid constr id generation (does not match pycardano)"
        )

    @given(st.data())
    def test_constant_index_list(self, data):
        xs = data.draw(st.lists(st.integers()))
        y = data.draw(
            st.one_of(
                st.integers(min_value=1 - len(xs), max_value=len(xs) - 1), st.integers()
            )
            if xs
            else st.integers()
        )
        # test the optimization for list access when the index is known at compile time
        source_code = f"""
from typing import Dict, List, Union
def validator(x: List[int]) -> int:
    return x[{y}]
            """
        try:
            exp = xs[y]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs)
        except Exception as e:
            ret = None
        self.assertEqual(ret, exp, "list index returned wrong value")

    def test_empty_return(self):
        source_code = """
def validator(_: None) -> None:
    return
"""
        res = eval_uplc(source_code, Unit())
        self.assertEqual(res, uplc.PlutusConstr(0, []), "Invalid return")

    @given(a=st.booleans(), b=st.booleans())
    def test_cast_bool_to_int_lt(self, a: bool, b: bool):
        source_code = """
def validator(a: bool, b:bool)-> int:
    return 5+(a<b)
"""
        res = eval_uplc_value(source_code, a, b)
        self.assertEqual(res, 5 + (a < b))

    @given(a=st.booleans(), b=st.booleans())
    def test_cast_bool_to_int_gt(self, a: bool, b: bool):
        source_code = """
def validator(a: bool, b:bool)-> int:
    return 5-(a>b)
"""
        res = eval_uplc_value(source_code, a, b)
        self.assertEqual(res, 5 - (a > b))

    @given(st.data())
    def test_index_access_skip(self, data):
        xs = data.draw(st.lists(st.integers()))
        y = data.draw(
            st.one_of(
                st.integers(min_value=1 - len(xs), max_value=len(xs) - 1), st.integers()
            )
            if xs
            else st.integers()
        )
        # test the optimization for list access when the index is known at compile time
        source_code = f"""
from typing import Dict, List, Union
def validator(x: List[int], y: int) -> int:
    return x[y]
            """
        try:
            exp = xs[y]
        except IndexError:
            exp = None
        config = DEFAULT_CONFIG
        config.update(fast_access_skip=5)
        try:
            ret = eval_uplc_value(source_code, xs, y, config=config)
        except Exception as e:
            ret = None
        self.assertEqual(ret, exp, "list index returned wrong value")

    def test_index_access_skip_faster(self):
        xs = list(range(1000))
        y = 250
        # test the optimization for list access when the list is long and we can skip entries
        source_code = f"""
from typing import Dict, List, Union
def validator(x: List[int], y: int) -> int:
    return x[y]
            """
        exp = xs[y]
        default_config = DEFAULT_CONFIG
        raw_ret_noskip = eval_uplc_raw(source_code, xs, y, config=default_config)
        skip_config = default_config.update(fast_access_skip=100)
        raw_ret_skip = eval_uplc_raw(source_code, xs, y, config=skip_config)
        self.assertEqual(
            raw_ret_noskip.result.value, exp, "list index returned wrong value"
        )
        self.assertEqual(
            raw_ret_skip.result.value, exp, "list index returned wrong value"
        )
        self.assertLess(
            raw_ret_skip.cost.cpu,
            raw_ret_noskip.cost.cpu,
            "skipping had adverse effect on cpu",
        )
        self.assertLess(
            raw_ret_skip.cost.memory,
            raw_ret_noskip.cost.memory,
            "skipping had adverse effect on memory",
        )

    def test_list_comprehension_non_boolean_filter(self):
        source_code = """
from opshin.prelude import *

def validator(a: List[int]) -> None:
    b = [x for x in a if x]  # x is an int, not a bool - now properly cast to bool
    pass
"""
        eval_uplc(source_code, [1, 0, 2, 0, 3])

    def test_list_comprehension_invalid_filter_type(self):
        source_code = """
from opshin.prelude import *
from dataclasses import dataclass

@dataclass()
class CustomClass(PlutusData):
    CONSTR_ID = 0
    value: int

def validator(a: List[CustomClass]) -> None:
    # This should fail because CustomClass cannot be cast to bool
    b = [x for x in a if x]  # x is CustomClass, which has no __bool__ method
    pass
"""
        # This should fail during compilation since CustomClass cannot be cast to bool
        with self.assertRaises(CompilerError) as context:
            builder._compile(source_code)
        self.assertIn("Can only create bools", str(context.exception))

    def test_tuple_comprehension_non_boolean_filter(self):
        source_code = """
from opshin.prelude import *

def validator(a: int) -> None:
    b = [x for x in (a, a+1) if x]  # x is an int, not a bool - now properly cast to bool
    pass
"""
        # should fail during compilation because tuple comprehension is not supported yet
        with self.assertRaises(CompilerError) as context:
            builder._compile(source_code)
        self.assertIn("iterating over", str(context.exception).lower())

    def test_tuple_type_correct_subtyping(self):
        source_code = """
def validator(a: int) -> int:
    t1 = (a, a, a)
    t2 = (a, a)
    
    t3 = t1 if a else t2
    
    return t3[2]
"""
        # this should fail during compilation because t3 is not guaranteed to have a third element
        with self.assertRaises(CompilerError) as context:
            builder._compile(source_code)
        self.assertIn("out of bounds", str(context.exception))

    def test_tuple_type_correct_subtyping_2(self):
        source_code = """
def validator(a: int) -> int:
    t1 = (a, a, a)
    t2 = (a, a)

    t3 = t1 if False else t2

    return t3[1]
"""
        # this should pass during compilation because t3 is guaranteed to have a second element
        x = eval_uplc_value(source_code, 2)
        self.assertEqual(x, 2)

    def test_import_integritycheck_reserved_name(self):
        source_code = """
from opshin.std.integrity import check_integrity as bytes

def validator(a: int) -> int:
    return a
    
"""
        try:
            builder._compile(source_code)
            self.fail("Integrity check did not catch reserved name")
        except Exception as e:
            self.assertIn(
                "reserved",
                str(e),
                "Integrity check did not catch reserved name",
            )

    def test_type_change_error_message(self):
        source_code = """
def validator(a: int) -> int:
    a = 1
    a = "hello"
    return a

"""
        try:
            builder._compile(source_code)
            self.fail("Type check did not fail")
        except Exception as e:
            assert "int" in str(e) and "str" in str(
                e
            ), "Type check did not fail with correct message"
