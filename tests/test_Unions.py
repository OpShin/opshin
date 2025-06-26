import unittest
import hypothesis
from hypothesis import given
from hypothesis import strategies as st
from .utils import eval_uplc_value, eval_uplc_raw
from . import PLUTUS_VM_PROFILE
from opshin.util import CompilerError

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)

from .test_misc import A
from typing import List, Dict

from opshin.ledger.api_v2 import *
from opshin import DEFAULT_CONFIG


def to_int(x):
    if isinstance(x, A):
        return 5
    elif isinstance(x, int):
        return 6
    elif isinstance(x, bytes):
        return 7
    elif isinstance(x, List):
        return 8
    elif isinstance(x, Dict):
        return 9
    return False


union_types = st.sampled_from([A(0), 10, b"foo", [1, 2, 3, 4, 5], {1: 2, 2: 3}])


class Union_tests(unittest.TestCase):
    @hypothesis.given(union_types)
    def test_Union_types(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[A, int, bytes, List[Anything], Dict[Anything, Anything]]) -> int:
    k: int = 0
    if isinstance(x, A):
        k = 5
    elif isinstance(x, bytes):
        k = 7
    elif isinstance(x, int):
        k = 6
    elif isinstance(x, List):
        k = 8
    elif isinstance(x, Dict):
        k = 9
    return k
"""
        res = eval_uplc_value(source_code, x)
        self.assertEqual(res, to_int(x))

    @hypothesis.given(union_types)
    def test_Union_types_different_order(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[A, int, bytes, List[Anything], Dict[Anything, Anything]]) -> int:
    k: int = 1
    if isinstance(x, int):
        k = 6
    elif isinstance(x, Dict):
        k = 9
    elif isinstance(x, bytes):
        k = 7
    elif isinstance(x, A):
        k = 5
    elif isinstance(x, List):
        k = 8
    return k
"""
        res = eval_uplc_value(source_code, x)
        self.assertEqual(res, to_int(x))

    @unittest.expectedFailure
    def test_incorrect_Union_types(
        self,
    ):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[A, bytes,]) -> int:
    k: int = 0
    if isinstance(x, A):
        k = 5
    elif isinstance(x, bytes):
        k = 7
    elif isinstance(x, int):
        k = 6
    return k
"""
        with self.AssertRaises(CompilerError):
            res = eval_uplc_value(source_code, 2)

    def test_isinstance_Dict_subscript_fail(
        self,
    ):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[A, int, bytes, List[Anything], Dict[Anything, Anything]]) -> int:
    k: int = 1
    if isinstance(x, int):
        k = 6
    elif isinstance(x, Dict[Anything, Anything]):
        k = 9
    elif isinstance(x, bytes):
        k = 7
    elif isinstance(x, A):
        k = 5
    elif isinstance(x, List):
        k = 8
    return k
"""
        with self.assertRaises(CompilerError) as ce:
            res = eval_uplc_value(source_code, [1, 2, 3])
        self.assertIsInstance(ce.exception.orig_err, TypeError)

    def test_isinstance_List_subscript_fail(
        self,
    ):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[A, int, bytes, List[Anything], Dict[Anything, Anything]]) -> int:
    k: int = 1
    if isinstance(x, int):
        k = 6
    elif isinstance(x, Dict):
        k = 9
    elif isinstance(x, bytes):
        k = 7
    elif isinstance(x, A):
        k = 5
    elif isinstance(x, List[Anything]):
        k = 8
    return k
"""
        with self.assertRaises(CompilerError) as ce:
            res = eval_uplc_value(source_code, [1, 2, 3])
        self.assertIsInstance(ce.exception.orig_err, TypeError)

    def test_Union_list_is_anything(
        self,
    ):
        """Test fails if List in union is anything other than List[Anything]"""
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[A, int, bytes, List[int], Dict[Anything, Anything]]) -> int:
    k: int = 1
    if isinstance(x, int):
        k = 6
    elif isinstance(x, Dict):
        k = 9
    elif isinstance(x, bytes):
        k = 7
    elif isinstance(x, A):
        k = 5
    elif isinstance(x, List):
        k = 8
    return k
"""
        with self.assertRaises(CompilerError) as ce:
            res = eval_uplc_value(source_code, [1, 2, 3])
        self.assertIsInstance(ce.exception.orig_err, AssertionError)

    def test_Union_dict_is_anything(
        self,
    ):
        """Test fails if Dict in union is anything other than Dict[Anything, Anything]"""
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[A, int, bytes, List[Anything], Dict[int, bytes]]) -> int:
    k: int = 1
    if isinstance(x, int):
        k = 6
    elif isinstance(x, Dict):
        k = 9
    elif isinstance(x, bytes):
        k = 7
    elif isinstance(x, A):
        k = 5
    elif isinstance(x, List):
        k = 8
    return k
"""
        with self.assertRaises(CompilerError) as ce:
            res = eval_uplc_value(source_code, [1, 2, 3])
        self.assertIsInstance(ce.exception.orig_err, AssertionError)

    def test_same_constructor_fail(self):
        @dataclass()
        class B(PlutusData):
            CONSTR_ID = 0
            foo: int

        @dataclass()
        class C(PlutusData):
            CONSTR_ID = 0
            foo: int

        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class B(PlutusData):
    CONSTR_ID = 0
    foo: int

@dataclass()
class C(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[B, C]) -> int:
    return 100
"""
        with self.assertRaises(CompilerError) as ce:
            res = eval_uplc_value(source_code, B(0))
        self.assertIsInstance(ce.exception.orig_err, AssertionError)

    def test_str_fail(self):
        source_code = """
def validator(x: Union[int, bytes, str]) -> int:
    if isinstance(x, int):
        return 5
    elif isinstance(x, bytes):
        return 6
    elif isinstance(x, str):
        return 7
    return 100
"""
        with self.assertRaises(CompilerError) as ce:
            res = eval_uplc_value(source_code, "test")
        self.assertIsInstance(ce.exception.orig_err, AssertionError)

    def test_bool_fail(self):
        source_code = """
def validator(x: Union[int, bytes, bool]) -> int:
    if isinstance(x, int):
        return 5
    elif isinstance(x, bytes):
        return 6
    elif isinstance(x, bool):
        return 7
    return 100
"""
        with self.assertRaises(CompilerError) as ce:
            res = eval_uplc_value(source_code, True)
        self.assertIsInstance(ce.exception.orig_err, AssertionError)

    @hypothesis.given(st.sampled_from([14, b""]))
    def test_Union_builtin_cast(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def validator(x: Union[int,bytes]) -> int:
    k: int = 0
    if isinstance(x, int):
        k = x+5
    elif isinstance(x, bytes):
        k = len(x)
    return k
"""
        res = eval_uplc_value(source_code, x)
        real = x + 5 if isinstance(x, int) else len(x)
        self.assertEqual(res, real)

    @hypothesis.given(st.sampled_from(range(14)))
    def test_Union_builtin_cast_internal(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def foo(x: Union[int,bytes]) -> int:
    k: int = 0
    if isinstance(x, int):
        k = x+5
    elif isinstance(x, bytes):
        k = len(x)
    return k

def validator(x: int) -> int:
    if x > 5:
        k = foo(x+1)
    else:
        k = foo(b"0"*x)
    return k
"""
        res = eval_uplc_value(source_code, x)
        real = x + 6 if x > 5 else len(b"0" * x)
        self.assertEqual(res, real)

    @hypothesis.given(st.sampled_from(range(14)))
    def test_Union_builtin_cast_direct(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def validator(x: int) -> int:
    y: Union[int,bytes] = 5 if x > 5 else b"0"*x
    k: int = 0
    if isinstance(y, int):
        k = y+1
    elif isinstance(y, bytes):
        k = len(y)
    return k
"""
        res = eval_uplc_value(source_code, x)
        real = 5 + 1 if x > 5 else len(b"0" * x)
        self.assertEqual(res, real)

    @hypothesis.given(st.sampled_from(range(14)))
    def test_Union_cast_ifexpr(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    x: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    y: bytes

def foo(x: Union[A, B]) -> int:
    k: int = x.x + 1 if isinstance(x, A) else len(x.y) 
    return k

def validator(x: int) -> int:
    if x > 5:
        k = foo(A(x))
    else:
        k = foo(B(b"0"*x))
    return k
"""
        res = eval_uplc_value(source_code, x)
        real = x + 1 if x > 5 else len(b"0" * x)
        self.assertEqual(res, real)

    @hypothesis.given(st.sampled_from(range(14)))
    def test_Union_builtin_cast_ifexpr(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def foo(x: Union[int, bytes]) -> int:
    k: int = x + 1 if isinstance(x, int) else len(x) 
    return k

def validator(x: int) -> int:
    if x > 5:
        k = foo(x+1)
    else:
        k = foo(b"0"*x)
    return k
"""
        res = eval_uplc_value(source_code, x)
        real = x + 2 if x > 5 else len(b"0" * x)
        self.assertEqual(res, real)

    @unittest.skip("Throw compilation error, hence not critical")
    @hypothesis.given(st.sampled_from(range(14)))
    def test_Union_cast_List(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    x: int

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    y: bytes

def foo(xs: List[Union[A, B]]) -> List[int]:
    k: List[int] = [x.x + 1 for x in xs if isinstance(x, A)]
    if not k:
        k = [len(x.y) for x in xs if isinstance(x, B)]
    return k

def validator(x: int) -> int:
    if x > 5:
        k = foo([A(x)])
    else:
        k = foo([B(b"0"*x)])
    return k[0]
"""
        res = eval_uplc_value(source_code, x)
        real = x + 1 if x > 5 else len(b"0" * x)
        self.assertEqual(res, real)

    @unittest.skip("Throw compilation error, hence not critical")
    @hypothesis.given(st.sampled_from(range(14)))
    def test_Union_builtin_cast_List(self, x):
        source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def foo(xs: List[Union[int, bytes]]) -> List[int]:
    k: List[int] = [x + 1 for x in xs if isinstance(x, int)]
    if not k:
        k = [len(x) for x in xs if isinstance(x, bytes)]
    return k

def validator(x: int) -> int:
    if x > 5:
        k = foo(x+1)
    else:
        k = foo(b"0"*x)
    return k[0]
"""
        res = eval_uplc_value(source_code, x)
        real = x + 2 if x > 5 else len(b"0" * x)
        self.assertEqual(res, real)

    def test_Union_expansion(
        self,
    ):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if isinstance(x, int):
        k = x + 1
    else:
        k = len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    k = x + 1
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, 4, config=euo_config)
        target = eval_uplc_raw(target_code, 4, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    @hypothesis.given(st.sampled_from(range(4, 7)))
    def test_Union_expansion_BoolOp(self, x):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if isinstance(x, int) and x > 5:
        k = x + 1
    elif isinstance(x, int):
        k = x - 1
    else:
        k = len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    if x > 5:
        k = x +1
    else:
        k = x - 1
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

    def test_Union_expansion_UnaryOp(
        self,
    ):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if not isinstance(x, int):
        k = len(x)
    else:
        k = x + 1
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    k = x + 1
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, 4, config=euo_config)
        target = eval_uplc_raw(target_code, 4, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    def test_Union_expansion_IfExp(
        self,
    ):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    k = x + 1 if isinstance(x, int) else len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    k = x + 1
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, 4, config=euo_config)
        target = eval_uplc_raw(target_code, 4, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    @given(x_in=st.sampled_from([4, b"123"]), y_in=st.sampled_from([4, b"123"]))
    def test_Union_expansion_multiple(self, x_in, y_in):
        x = type(x_in).__name__
        y = type(y_in).__name__
        source_code = f"""
from typing import Dict, List, Union

def foo(x: Union[int, bytes], y: Union[int, bytes]) -> int:
    if isinstance(x, int):
        if isinstance(y, int):
            k = x + y
        else:
            k = x + len(y)
    else:
        if isinstance(y, int):
            k = len(x) + y
        else:
            k = len(x) + len(y)
    return k

def validator(x: {x}, y: {y} ) -> int:
    return foo(x, y)
"""
        target_code = f"""
from typing import Dict, List, Union

def foo(x: {x}, y: {y} ) -> int:
    k = {'len(x)' if x=='bytes' else 'x'} + {'len(y)' if y == 'bytes' else 'y'}
    return k

def validator(x: {x},  y: {y}) -> int:
    return foo(x, y)
"""
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, x_in, y_in, config=euo_config)
        target = eval_uplc_raw(target_code, x_in, y_in, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)
