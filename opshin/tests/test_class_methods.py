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

    def test_invalid_python(self, x=5, y=6):
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

    @given(x=st.integers(), y=st.integers())
    def test_Self_arguments(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __ge__(self, other: Self) -> bool:
        return self.a >= other.a

def validator(a: int, b: int) -> bool:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 >= foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x >= y)

    def test_Self_return(self):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def get_me(self) -> Self:
        return self

def validator(b:int) -> int:
    foo1 = Foo(b)
    return foo1.get_me().a
"""
        ret = eval_uplc_value(source_code, 5)
        self.assertEqual(ret, 5)

    @given(x=st.integers(), y=st.integers())
    def test_externally_bound_variables_scope(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def larger(self, other:Self) -> Self:
        if self.a>other.a:
            return self
        else:
            return other

def validator(a:int, b:int) -> int:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1.larger(foo2).a
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, max(x, y))

    @given(x=st.integers(), y=st.integers())
    def test_eq_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __eq__(self, other:Self) -> bool:
        return self.a==other.a

def validator(a:int, b:int) -> bool:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 == foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x == y)

    @given(x=st.integers(), y=st.integers())
    def test_ne_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __ne__(self, other:Self) -> bool:
        return self.a!=other.a

def validator(a:int, b:int) -> bool:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 != foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x != y)

    @given(x=st.integers(), y=st.integers())
    def test_lt_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __lt__(self, other:Self) -> bool:
        return self.a<other.a

def validator(a:int, b:int) -> bool:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 < foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x < y)

    @given(x=st.integers(), y=st.integers())
    def test_le_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __le__(self, other:Self) -> bool:
        return self.a<=other.a

def validator(a:int, b:int) -> bool:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 <= foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x <= y)

    @given(x=st.integers(), y=st.integers())
    def test_gt_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __gt__(self, other:Self) -> bool:
        return self.a>other.a

def validator(a:int, b:int) -> bool:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 > foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x > y)

    @given(x=st.integers(), y=st.integers())
    def test_ge_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __ge__(self, other:Self) -> bool:
        return self.a>=other.a

def validator(a:int, b:int) -> bool:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 >= foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x >= y)

    @given(x=st.integers(), y=st.integers())
    def test_add_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __add__(self, other:Self) -> int:
        return self.a + other.a

def validator(a:int, b:int) -> int:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 + foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x + y)

    @given(x=st.integers(), y=st.integers())
    def test_sub_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __sub__(self, other:Self) -> int:
        return self.a - other.a

def validator(a:int, b:int) -> int:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 - foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x - y)

    @given(x=st.integers(), y=st.integers())
    def test_mul_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __mul__(self, other:Self) -> int:
        return self.a * other.a

def validator(a:int, b:int) -> int:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 * foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x * y)

    @given(x=st.integers(), y=st.integers().filter(lambda x: x != 0))
    def test_floordiv_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __floordiv__(self, other:Self) -> int:
        return self.a // other.a

def validator(a:int, b:int) -> int:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 // foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x // y)

    @given(x=st.integers(), y=st.integers().filter(lambda x: x != 0))
    def test_mod_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __mod__(self, other:Self) -> int:
        return self.a % other.a

def validator(a:int, b:int) -> int:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 % foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x % y)

    @given(
        x=st.integers(min_value=-1000, max_value=1000),
        y=st.integers(min_value=0, max_value=4),
    )
    def test_pow_dunder(self, x: int, y: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int

    def __pow__(self, other:Self) -> int:
        return self.a ** other.a

def validator(a:int, b:int) -> int:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 ** foo2
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x**y)

    @given(x=st.integers(), y=st.integers(), z=st.integers(), a=st.integers())
    def test_matmul_dunder(self, x: int, y: int, z: int, a: int):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int
    b: int
    
    def __matmul__(self, other:Self) -> int:
        return self.a * other.a + self.b*other.b

def validator(a:int, b:int, c: int, d:int) -> int:
    foo1 = Foo(a,b)
    foo2 = Foo(c,d)
    return foo1 @ foo2
"""
        ret = eval_uplc_value(source_code, x, y, z, a)
        self.assertEqual(ret, x * z + y * a)

    def test_unsupported_dunder(
        self,
    ):
        source_code = """
from typing import Self
from opshin.prelude import *
@dataclass()
class Foo(PlutusData):
    a: int
    def __init__(self) -> None:
        pass

    def __add__(self, other:Self) -> int:
        return self.a + other.a

def validator(a:int, b:int) -> int:
    foo1 = Foo(a)
    foo2 = Foo(b)
    return foo1 + foo2
"""
        with self.assertRaises(CompilerError):
            ret = eval_uplc_value(source_code, 5, 6)
