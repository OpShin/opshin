import unittest
from dataclasses import dataclass
import hypothesis
from hypothesis import given
from hypothesis import strategies as st

from pycardano import PlutusData
from uplc import ast as uplc

from opshin import DEFAULT_CONFIG, builder, CompilerError
from tests.utils import eval_uplc_value, Unit, eval_uplc, eval_uplc_raw

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

    def test_constant_folding_disabled(self):
        source_code = """
from opshin.prelude import *

def validator(_: None) -> bytes:
    return bytes.fromhex("0011")
"""
        with self.assertRaises(CompilerError):
            eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG)

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
        code_dumped = code.dumps()
        self.assertTrue(
            "(con (list (pair data data)) [(B #73, I 1), (B #6d, I 0)])" in code_dumped
            or "(con data (Map [(B #73, I 1), (B #6d, I 0)]))" in code_dumped
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
        self.assertTrue(
            "(con integer 55)" in code.dumps() or "(con data (I 55))" in code.dumps()
        )
        res = eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)
        if isinstance(res, Exception):
            raise res
        self.assertEqual(
            res.value,
            55,
        )

    def test_constant_folding_ifelse(self):
        source_code = """
def validator(_: None) -> int:
    if False:
        a = 10
    return a
"""
        with self.assertRaises(RuntimeError):
            eval_uplc(source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    def test_constant_folding_for(self):
        source_code = """
from typing import List
def validator(x: List[int]) -> int:
    for i in x:
        a = 10
    return a
"""
        with self.assertRaises(RuntimeError):
            eval_uplc(source_code, [], config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    def test_constant_folding_for_target(self):
        source_code = """
from typing import List
def validator(x: List[int]) -> int:
    for i in x:
        a = 10
    return i
"""
        with self.assertRaises(RuntimeError):
            eval_uplc(source_code, [], config=DEFAULT_CONFIG_CONSTANT_FOLDING)

    def test_constant_folding_while(self):
        source_code = """
def validator(_: None) -> int:
    while False:
        a = 10
    return a
"""
        with self.assertRaises(RuntimeError):
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
        self.assertTrue(
            "(con integer 10)" in code.dumps() or "(con data (I 10))" in code.dumps()
        )

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
        self.assertTrue(
            "(con integer 10)" in code.dumps() or "(con data (I 10))" in code.dumps()
        )

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
        self.assertTrue(
            f"(con integer {2**10})" in code_src
            or f"(con data (I {2**10}))" in code_src
        )

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
        res = eval_uplc_value(
            source_code, Unit(), config=DEFAULT_CONFIG_CONSTANT_FOLDING
        )
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
from typing import Dict, List, Union
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
from typing import Dict, List, Union
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

    @hypothesis.given(st.sampled_from(range(4, 7)))
    def test_Union_expansion_BoolOp_or_all(self, x):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if isinstance(x, bytes) or isinstance(x, int):
        k = 2
    else:
        k = len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    k = 2
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, x, config=euo_config)
        target = eval_uplc_raw(target_code, x, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    def test_type_inference_list_3(self):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: int) -> Union[int, bytes]:
    l = [10, b"hello"]
    return l[x]
"""
        # primarily test that this does not fail to compile
        res = eval_uplc_value(source_code, 0)
        self.assertEqual(res, 10)
        res = eval_uplc_value(source_code, 1)
        self.assertEqual(res, b"hello")

    def test_compilation_deterministic_local_19_examples_smart_contracts_liquidity_pool_py(
        self,
    ):
        input_file = "examples/smart_contracts/liquidity_pool.py"
        with open(input_file) as fp:
            source_code = fp.read()
        code = builder._compile(source_code)
        for i in range(10):
            code_2 = builder._compile(source_code)
            self.assertEqual(code.dumps(), code_2.dumps())
