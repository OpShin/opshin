import unittest
import hypothesis
from hypothesis import given
from hypothesis import strategies as st
from .utils import eval_uplc_value
from . import PLUTUS_VM_PROFILE
from opshin.util import CompilerError

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)

from .test_misc import A
from typing import List, Dict

from opshin.ledger.api_v2 import *


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
