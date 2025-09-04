import unittest
from dataclasses import dataclass

from pycardano import PlutusData
from uplc import ast as uplc

from opshin import DEFAULT_CONFIG, builder
from tests.utils import eval_uplc_value, Unit, eval_uplc

DEFAULT_CONFIG_CONSTANT_FOLDING = DEFAULT_CONFIG.update(constant_folding=True)


class ConstantFoldingTest(unittest.TestCase):
    def test_constant_folding(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> bytes:
    return bytes.fromhex("0011")
"""
        res = eval_uplc_value(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertEqual(res, bytes.fromhex("0011"))

    @unittest.expectedFailure
    def test_constant_folding_disabled(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> bytes:
    return bytes.fromhex("0011")
"""
        eval_uplc(source_code, Unit(), constant_folding=False)

    def test_constant_folding_list(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> List[int]:
    return list(range(0, 10, 2))
"""
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertIn("(con (list integer) [0, 2, 4, 6, 8])", code.dumps())
        res = builder.uplc_eval(code).result
        self.assertEqual(
            res,
            uplc.PlutusList([uplc.PlutusInteger(i) for i in range(0, 10, 2)]),
        )

    def test_constant_folding_dict(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> Dict[str, bool]:
    return {"s": True, "m": False}
"""
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertIn(
            "(con (list (pair data data)) [(B #73, I 1), (B #6d, I 0)])", code.dumps()
        )
        res = eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)
        if isinstance(res, Exception):
            raise res
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
        res = eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)
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
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertIn("(con data (Constr 0 [B #0011]))", code.dumps())
        res = eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)
        self.assertEqual(
            res,
            uplc.PlutusConstr(
                constructor=0, fields=[uplc.PlutusByteString(value=b"\x00\x11")]
            ),
        )

    def test_constant_folding_plutusdata_list(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> List[PubKeyCredential]:
    return [PubKeyCredential(bytes.fromhex("0011"))]
"""
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertIn("(con (list data) [Constr 0 [B #0011]])", code.dumps())
        res = eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)
        self.assertEqual(
            res,
            uplc.PlutusList(
                [
                    uplc.PlutusConstr(
                        constructor=0, fields=[uplc.PlutusByteString(value=b"\x00\x11")]
                    )
                ]
            ),
        )

    def test_constant_folding_user_def(self):
        source_code = """
def fib(i: int) -> int:
    return i if i < 2 else fib(i-1) + fib(i-2)

def validator(_: None) -> int:
    return fib(10)
"""
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertIn("(con integer 55)", code.dumps())
        res = eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)
        if isinstance(res, Exception):
            raise res
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
        eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    @unittest.expectedFailure
    def test_constant_folding_for(self):
        source_code = """
def validator(x: List[int]) -> int:
    for i in x:
        a = 10
    return a
"""
        eval_uplc(source_code, [], config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    @unittest.expectedFailure
    def test_constant_folding_for_target(self):
        source_code = """
def validator(x: List[int]) -> int:
    for i in x:
        a = 10
    return i
"""
        eval_uplc(source_code, [], config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    @unittest.expectedFailure
    def test_constant_folding_while(self):
        source_code = """
def validator(_: None) -> int:
    while False:
        a = 10
    return a
"""
        eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)

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
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
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
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
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
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertIn("(con integer 10)", code.dumps())

    def test_constant_folding_repeated_assign(self):
        source_code = """
def validator(i: int) -> int:
    a = 4
    for k in range(i):
        a = 2
    return a
"""
        res = eval_uplc(
            source_code, uplc.PlutusInteger(0), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        if isinstance(res, Exception):
            raise res
        self.assertEqual(res.value, 4)
        res = eval_uplc(
            source_code, uplc.PlutusInteger(1), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        if isinstance(res, Exception):
            raise res
        self.assertEqual(res.value, 2)

    def test_constant_folding_math(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> int:
    return 2 ** 10
"""
        code = builder._compile(source_code, config=DEFAULT_CONFIG_CONSTANT_FOLDING)
        code_src = code.dumps()
        self.assertIn(f"(con integer {2**10})", code_src)

    def test_constant_folding_ignore_reassignment(self):
        source_code = """
b = int
def validator(_: None) -> int:
    def int(a) -> b:
        return 2
    return int(5)
"""
        res = eval_uplc_value(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertEqual(res, 2)

    def test_constant_folding_no_print_eval(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> None:
    return print("hello")
"""
        code = builder._compile(source_code, config=DEFAULT_CONFIG_CONSTANT_FOLDING)
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
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, 2)

    def test_double_import_offset(self):
        source_code = """
from opshin.ledger.api_v2 import *
from opshin.prelude import *

def validator(
    d: Nothing,
    r: Nothing,
    context: ScriptContext,
):
    house_address = Address(
        payment_credential=PubKeyCredential(
            credential_hash=b""
        ),
        staking_credential=SomeStakingCredential(
            staking_credential=StakingHash(
                value=PubKeyCredential(
                    credential_hash=b""
                )
            )
        ),
    )
"""
        # would fail because Address is assigned multiple times and then not constant folded
        # TODO find a better way
        builder._compile(source_code, config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    def test_double_import_direct(self):
        source_code = """
from opshin.prelude import *
from opshin.prelude import *

def validator(
    d: Nothing,
    r: Nothing,
    context: ScriptContext,
):
    house_address = Address(
        payment_credential=PubKeyCredential(
            credential_hash=b""
        ),
        staking_credential=SomeStakingCredential(
            staking_credential=StakingHash(
                value=PubKeyCredential(
                    credential_hash=b""
                )
            )
        ),
    )
"""
        # would fail because Address is assigned multiple times and then not constant folded
        # TODO find a better way
        builder._compile(source_code, config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    def test_double_import_deep(self):
        source_code = """
from opshin.ledger.interval import *
from opshin.prelude import *

def validator(
    d: Nothing,
    r: Nothing,
    context: ScriptContext,
):
    house_address = Address(
        payment_credential=PubKeyCredential(
            credential_hash=b""
        ),
        staking_credential=SomeStakingCredential(
            staking_credential=StakingHash(
                value=PubKeyCredential(
                    credential_hash=b""
                )
            )
        ),
    )
"""
        # would fail because Address is assigned multiple times and then not constant folded
        # TODO find a better way
        builder._compile(source_code, config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    def test_empty_list_int_constant_folding(self):
        source_code = """
def validator(_: None) -> List[int]:
    a: List[int] = []
    return a
"""
        res = eval_uplc_value(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertEqual(res, [])

    def test_empty_dict_int_int_constant_folding(self):
        source_code = """
def validator(_: None) -> Dict[int, int]:
    a: Dict[int, int] = {}
    return a
"""
        res = eval_uplc_value(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertEqual(res, {})

    def test_empty_dict_displaced_constant_folding(self):
        source_code = """
from typing import Dict, List, Union

VAR: Dict[bytes, int] = {}

def validator(b: Dict[int, Dict[bytes, int]]) -> Dict[bytes, int]:
    a = b.get(0, VAR)
    return a
        """
        res = eval_uplc_value(
            source_code, {1: {b"": 0}}, config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertEqual(res, {})

    def test_constant_folding_bytestring_index(self):
        source_code = """
def validator(x: bytes) -> int:
    return x[0 + 2] + 5
"""
        code = builder._compile(source_code, Unit(), config=DEFAULT_CONFIG)
        assert "lengthOfByteString" in code.dumps(), "Needs to check length at runtime"
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        assert (
            "lengthOfByteString" not in code.dumps()
        ), "Should be constant folded, can precompute that length not needed"

    def test_constant_folding_bytestring_index_negative(self):
        source_code = """
def validator(x: bytes) -> int:
    return x[0 - 2] + 5
"""
        code = builder._compile(source_code, Unit(), config=DEFAULT_CONFIG)
        assert "lengthOfByteString" in code.dumps(), "Needs to check length at runtime"
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        assert (
            "lengthOfByteString" in code.dumps()
        ), "Should be constant folded, but still needs to check length at runtime"

    def test_constant_folding_check_integrity(self):
        """
        Check_integrity does not exist at runtime, so will create a  value error.
        However, applying check_integrity to a constant is always non-failing/true because
        constants are always well-formed.
        """
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(_: B) -> None:
    check_integrity(B(4,5))
        """
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertNotIn("ValueError", code.dumps())
        eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    def test_constant_folding_check_integrity_nonconst(self):
        """
        Check_integrity is just pass in Python, but should not be optimized away
        """
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: B) -> None:
    check_integrity(x)
        """
        code = builder._compile(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
        self.assertIn("ValueError", code.dumps())
        try:
            eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)
        except Exception as e:
            pass

        @dataclass()
        class B(PlutusData):
            CONSTR_ID = 1
            foobar: int
            bar: int

        try:
            eval_uplc(source_code, B(4, 5), config=DEFAULT_CONFIG_CONSTANT_FOLDING)
        except Exception as e:
            self.fail("Should not raise")
