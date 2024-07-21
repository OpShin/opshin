import unittest

import hypothesis
from hypothesis import given
from hypothesis import strategies as st
from .utils import eval_uplc_value
from . import PLUTUS_VM_PROFILE
from opshin.util import CompilerError

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)


class Classmethod_tests(unittest.TestCase):
    @given(x=st.integers(), y=st.integers())
    def test_accessible_attributes(self, x: int, y: int):
        source_code = """
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int
    b: int

    def sum(self) -> int:
        return self.a + self.b

def validator(a: int, b: int) -> int:
    foo = Foo(a, b)
    return foo.sum()
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x + y)

    def test_instance_method_only(self, x=5, y=6):
        source_code = """
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int
    b: int

    def sum(self) -> int:
        return self.a + self.b

def validator(a: int, b: int) -> int:
    return Foo.sum()
"""
        with self.assertRaises(Exception):
            ret = eval_uplc_value(source_code, x, y)

    @given(x=st.integers(), y=st.integers())
    def test_ge_dunder(self, x: int, y: int):
        source_code = """
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __ge__(self, other: int) -> bool:
        return self.a >= other

def validator(a: int, b: int) -> bool:
    foo1 = Foo(a)
    return foo1 >= b
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x >= y)

    @given(x=st.integers(), y=st.integers())
    def test_le_dunder(self, x: int, y: int):
        source_code = """
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __le__(self, other:int) -> bool:
        return self.a <= other

def validator(a: int, b: int) -> bool:
    foo1 = Foo(a)
    return foo1 <= b
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x <= y)

    @given(x=st.integers(), y=st.integers())
    def test_invalid_python(self, x: int, y: int):
        source_code = """
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __ge__(self, other: Foo) -> bool:
        return self.a >= other.a

def validator(a: int, b: int) -> bool:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 >= foo2
"""
        with self.assertRaises(CompilerError):
            ret = eval_uplc_value(source_code, x, y)
