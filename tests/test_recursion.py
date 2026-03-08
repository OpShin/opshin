import unittest

from opshin import CompilerError, builder

from .utils import DEFAULT_TEST_CONFIG, Unit, eval_uplc_raw, eval_uplc_value


class RecursionTest(unittest.TestCase):
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

    def test_recursion_illegal(self):
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
        with self.assertRaises(CompilerError):
            eval_uplc_value(source_code, Unit())

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

    def test_self_recursion_via_alias(self):
        source_code = """
def validator(_: None) -> int:
    def f(n: int) -> int:
        if n == 0:
            return 0
        g = f
        return g(n - 1)
    return f(2)
        """
        self.assertEqual(0, eval_uplc_value(source_code, Unit()))

    def test_mutual_recursion_via_alias(self):
        source_code = """
def even(n: int) -> bool:
    if n == 0:
        return True
    f = odd
    return f(n - 1)

def odd(n: int) -> bool:
    if n == 0:
        return False
    g = even
    return g(n - 1)

def validator(n: int) -> int:
    return 1 if even(n) else 0
        """
        self.assertEqual(1, eval_uplc_value(source_code, 4))

    def test_forward_function_alias_capture(self):
        source_code = """
def validator(n: int) -> int:
    def inc(x: int) -> int:
        return plus_one(x)

    plus_one = add1

    def add1(x: int) -> int:
        return x + 1

    return inc(n)
        """
        self.assertEqual(5, eval_uplc_value(source_code, 4))

    def test_nested_union_expansion_mutual_recursion_cost(self):
        source_code = """
from typing import Union

def validator(x: bytes, n: int) -> int:
    def even_i(v: Union[int, bytes], n: int) -> int:
        if n == 0:
            if isinstance(v, int):
                return v
            if isinstance(v, bytes):
                return len(v)
        if isinstance(v, bytes):
            return odd_i(v[2:], n - 1)
        else:
            return odd_i(v + 1, n - 1)

    def odd_i(v: Union[int, bytes], n: int) -> int:
        if n == 0:
            if isinstance(v, int):
                return v + 100
            if isinstance(v, bytes):
                return len(v) + 100
        if isinstance(v, bytes):
            return even_i(len(v[2:]), n - 1)
        else:
            return even_i(bytes([v + 1]), n - 1)

    return even_i(x, n)
        """
        target_code = """
def validator(x: bytes, n: int) -> int:
    def even_i_int(v: int, n: int) -> int:
        if n == 0:
            return v
        else:
            return odd_i_int(v + 1, n - 1)

    def odd_i_int(v: int, n: int) -> int:
        if n == 0:
            return v + 100
        else:
            return even_i_bytes(bytes([v + 1]), n - 1)

    def even_i_bytes(v: bytes, n: int) -> int:
        if n == 0:
            return len(v)
        else:
            return odd_i_bytes(v[2:], n - 1)

    def odd_i_bytes(v: bytes, n: int) -> int:
        if n == 0:
            return len(v) + 100
        else:
            return even_i_int(len(v[2:]), n - 1)

    return even_i_bytes(x, n)
        """
        config = DEFAULT_TEST_CONFIG
        expanded = eval_uplc_raw(
            source_code, b"abcd", 2, config=config.update(expand_union_types=True)
        )
        target = eval_uplc_raw(target_code, b"abcd", 2, config=config)

        self.assertEqual(expanded.result, target.result)
        self.assertLessEqual(expanded.cost.cpu, target.cost.cpu)
        self.assertLessEqual(expanded.cost.memory, target.cost.memory)

    def test_mutual_recursion_forward_declaration(self):
        source_code = """
def even(n: int) -> bool:
    if n == 0:
        return True
    return odd(n - 1)

def odd(n: int) -> bool:
    if n == 0:
        return False
    return even(n - 1)

def validator(n: int) -> int:
    return 1 if even(n) else 0
        """
        self.assertEqual(1, eval_uplc_value(source_code, 4))
        self.assertEqual(0, eval_uplc_value(source_code, 3))

    def test_nested_mutual_recursion_forward_declaration(self):
        source_code = """
def validator(n: int) -> int:
    def even(x: int) -> bool:
        if x == 0:
            return True
        return odd(x - 1)

    def odd(x: int) -> bool:
        if x == 0:
            return False
        return even(x - 1)

    return 1 if even(n) else 0
        """
        self.assertEqual(1, eval_uplc_value(source_code, 4))
        self.assertEqual(0, eval_uplc_value(source_code, 3))

    def test_three_function_recursion_cycle(self):
        source_code = """
def a(n: int) -> int:
    if n <= 0:
        return 1
    return b(n - 1)

def b(n: int) -> int:
    if n <= 0:
        return 2
    return c(n - 1)

def c(n: int) -> int:
    if n <= 0:
        return 3
    return a(n - 1)

def validator(n: int) -> int:
    return a(n)
        """
        self.assertEqual(1, eval_uplc_value(source_code, 0))
        self.assertEqual(2, eval_uplc_value(source_code, 1))
        self.assertEqual(3, eval_uplc_value(source_code, 2))
        self.assertEqual(1, eval_uplc_value(source_code, 3))

    def test_five_function_recursion_cycle(self):
        source_code = """
def a(n: int) -> int:
    if n <= 0:
        return 1
    return b(n - 1)

def b(n: int) -> int:
    if n <= 0:
        return 2
    return c(n - 1)

def c(n: int) -> int:
    if n <= 0:
        return 3
    return d(n - 1)

def d(n: int) -> int:
    if n <= 0:
        return 4
    return e(n - 1)

def e(n: int) -> int:
    if n <= 0:
        return 5
    return a(n - 1)

def validator(n: int) -> int:
    return a(n)
        """
        self.assertEqual(1, eval_uplc_value(source_code, 0))
        self.assertEqual(2, eval_uplc_value(source_code, 1))
        self.assertEqual(3, eval_uplc_value(source_code, 2))
        self.assertEqual(4, eval_uplc_value(source_code, 3))
        self.assertEqual(5, eval_uplc_value(source_code, 4))
        self.assertEqual(1, eval_uplc_value(source_code, 5))

    def test_forward_global_variable_in_function(self):
        source_code = """
def read_x() -> int:
    return x + 1

x: int = 41

def validator(_: None) -> int:
    return read_x()
        """
        self.assertEqual(42, eval_uplc_value(source_code, Unit()))

    def test_forward_class_reference_in_function(self):
        source_code = """
from opshin.prelude import *

def mk(v: int) -> MyData:
    return MyData(v)

@dataclass()
class MyData(PlutusData):
    value: int

def validator(_: None) -> int:
    return mk(2).value
        """
        self.assertEqual(2, eval_uplc_value(source_code, Unit()))

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
