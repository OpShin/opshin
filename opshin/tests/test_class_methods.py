import unittest

import hypothesis
from hypothesis import given
from hypothesis import strategies as st
from .utils import eval_uplc_value
from . import PLUTUS_VM_PROFILE


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

    @given(x=st.integers(), y=st.integers())
    def test_instance_method_only(self, x: int, y: int):
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
