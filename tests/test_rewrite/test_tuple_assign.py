import unittest

from hypothesis import given
from hypothesis import strategies as st

from opshin import builder
from opshin.util import CompilerError
from tests.utils import eval_uplc_raw, eval_uplc_value, Unit


class TupleAssignTest(unittest.TestCase):

    def test_tuple_assign_too_many(self):
        source_code = """
def validator(a: int) -> int:
    t1, t2 = (a, a+1, a+2)
    return t2
    """
        try:
            builder._compile(source_code)
            self.fail("Expected compilation failure due to tuple unpacking mismatch")
        except CompilerError as e:
            self.assertIn(
                "too many values to unpack", str(e).lower(), "Unexpected error message"
            )

    def test_tuple_assign_too_few(self):
        source_code = """
def validator(a: int) -> int:
    t1, t2, t3 = (a, a+1)
    return t2
    """
        try:
            builder._compile(source_code)
            self.fail("Expected compilation failure due to tuple unpacking mismatch")
        except CompilerError as e:
            self.assertIn(
                "not enough values to unpack",
                str(e).lower(),
                "Unexpected error message",
            )

    def test_tuple_assign_no_tuple(self):
        source_code = """
def validator(a: int) -> int:
    t1, t2 = a
    return t2
    """
        try:
            builder._compile(source_code)
            self.fail("Expected compilation failure due to tuple unpacking mismatch")
        except CompilerError as e:
            self.assertIn("deconstruction", str(e).lower(), "Unexpected error message")

    def test_tuple_assign_pair(self):
        source_code = """
def validator(a: int) -> int:
    x = {"a": a, "b": a + 1}
    t1, t2 = x.items()[0]
    return t2
    """
        builder._compile(source_code)

    def test_tuple_assign_pair_too_few(self):
        source_code = """
def validator(a: int) -> int:
    x = {"a": a, "b": a + 1}
    (t1,) = x.items()[0]
    return t1
    """
        try:
            builder._compile(source_code)
            self.fail("Expected compilation failure due to tuple unpacking mismatch")
        except CompilerError as e:
            self.assertIn(
                "too many values to unpack", str(e).lower(), "Unexpected error message"
            )

    def test_tuple_assign_pair_too_many(self):
        source_code = """
def validator(a: int) -> int:
    x = {"a": a, "b": a + 1}
    (t1,t2,t3) = x.items()[0]
    return t2
    """
        try:
            builder._compile(source_code)
            self.fail("Expected compilation failure due to tuple unpacking mismatch")
        except CompilerError as e:
            self.assertIn(
                "not enough values to unpack",
                str(e).lower(),
                "Unexpected error message",
            )

    def test_tuple_loop_assign_pair(self):
        source_code = """
def validator(a: int) -> int:
    x = {"a": a, "b": a + 1}
    for t1, t2 in x.items():
      pass
    return t2
    """
        builder._compile(source_code)

    def test_tuple_loop_assign_pair_too_few(self):
        source_code = """
def validator(a: int) -> str:
    x = {"a": a, "b": a + 1}
    for (t1,) in x.items():
      pass
    return t1
    """
        try:
            builder._compile(source_code)
            self.fail("Expected compilation failure due to tuple unpacking mismatch")
        except CompilerError as e:
            self.assertIn(
                "too many values to unpack", str(e).lower(), "Unexpected error message"
            )

    def test_tuple_loop_assign_pair_too_many(self):
        source_code = """
def validator(a: int) -> int:
    x = {"a": a, "b": a + 1}
    for (t1,t2,t3) in x.items():
      pass
    return t2
    """
        try:
            builder._compile(source_code)
            self.fail("Expected compilation failure due to tuple unpacking mismatch")
        except CompilerError as e:
            self.assertIn(
                "not enough values to unpack",
                str(e).lower(),
                "Unexpected error message",
            )

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_items_values_deconstr(self, xs):
        # asserts that deconstruction of parameters works for for loops too
        source_code = """
from typing import Dict, List, Union
def validator(xs: Dict[int, bytes]) -> bytes:
    sum_values = b""
    for _, x in xs.items():
        sum_values += x
    return sum_values
"""
        ret = eval_uplc_value(source_code, xs)
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
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(
            ret,
            1 + 2 + 3 + 4,
            "for loop deconstruction did not behave as expected",
        )

    @given(xs=st.lists(st.integers(), min_size=3, max_size=3))
    def test_list_assign(self, xs):
        source_code = """
from typing import List

def validator(xs: List[int]) -> int:
    a, b, c = xs
    return a + b + c
"""
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(ret, sum(xs), "list deconstruction did not behave as expected")

    @given(xs=st.lists(st.integers(), max_size=1))
    def test_list_assign_too_few(self, xs):
        source_code = """
from typing import List

def validator(xs: List[int]) -> int:
    a, b = xs
    return a + b
"""
        with self.assertRaises(Exception) as exc:
            eval_uplc_value(source_code, xs)
        self.assertIn("error", str(exc.exception).lower())

    @given(xs=st.lists(st.integers(), min_size=3, max_size=10))
    def test_list_assign_too_many(self, xs):
        source_code = """
from typing import List

def validator(xs: List[int]) -> int:
    a, b = xs
    return a + b
"""
        with self.assertRaises(Exception) as exc:
            eval_uplc_value(source_code, xs)
        self.assertIn("error", str(exc.exception).lower())

    def test_list_assign_compiles_to_linear_walk(self):
        source_code = """
from typing import List

def validator(xs: List[int]) -> int:
    a, b, c = xs
    return a + b + c
"""
        code = builder._compile(source_code)
        dumped = code.dumps()
        self.assertIn("headList", dumped)
        self.assertIn("tailList", dumped)
        self.assertNotIn("indexList", dumped.lower())

    def test_list_assign_large_deconstruction_improves_budget(self):
        source_code = """
from typing import List

def validator(xs: List[int]) -> int:
    a, b, c, d, e, f, g, h, i, j = xs
    return a + b + c + d + e + f + g + h + i + j
"""
        baseline_source_code = """
from typing import List

def validator(xs: List[int]) -> int:
    tmp = xs
    a = tmp[0]
    b = tmp[1]
    c = tmp[2]
    d = tmp[3]
    e = tmp[4]
    f = tmp[5]
    g = tmp[6]
    h = tmp[7]
    i = tmp[8]
    j = tmp[9]
    return a + b + c + d + e + f + g + h + i + j
"""
        optimized = eval_uplc_raw(source_code, list(range(1, 11)))
        baseline = eval_uplc_raw(baseline_source_code, list(range(1, 11)))
        self.assertLess(
            optimized.cost.cpu,
            baseline.cost.cpu,
            "list destructuring should beat repeated indexed access on cpu for large deconstructions",
        )
        self.assertLess(
            optimized.cost.memory,
            baseline.cost.memory,
            "list destructuring should beat repeated indexed access on memory for large deconstructions",
        )

    def test_tuple_assign_improves_budget(self):
        source_code = """
def validator(x: int) -> int:
    a, b, c, d, e, f, g, h, i, j = (
        x,
        x + 1,
        x + 2,
        x + 3,
        x + 4,
        x + 5,
        x + 6,
        x + 7,
        x + 8,
        x + 9,
    )
    return a + b + c + d + e + f + g + h + i + j
"""
        baseline_source_code = """
def validator(x: int) -> int:
    tmp = (x, x + 1, x + 2, x + 3, x + 4, x + 5, x + 6, x + 7, x + 8, x + 9)
    a = tmp[0]
    b = tmp[1]
    c = tmp[2]
    d = tmp[3]
    e = tmp[4]
    f = tmp[5]
    g = tmp[6]
    h = tmp[7]
    i = tmp[8]
    j = tmp[9]
    return a + b + c + d + e + f + g + h + i + j
"""
        optimized = eval_uplc_raw(source_code, 1)
        baseline = eval_uplc_raw(baseline_source_code, 1)
        self.assertLess(
            optimized.cost.cpu,
            baseline.cost.cpu,
            "tuple destructuring should beat repeated tuple indexing on cpu",
        )
        self.assertLess(
            optimized.cost.memory,
            baseline.cost.memory,
            "tuple destructuring should beat repeated tuple indexing on memory",
        )

    @given(x=st.integers(), y=st.integers())
    def test_astuple_assign(self, x, y):
        source_code = """
from dataclasses import dataclass, astuple
from opshin.prelude import *

@dataclass
class Pair(PlutusData):
    CONSTR_ID = 0
    x: int
    y: int

def validator(x: int, y: int) -> int:
    a, b = astuple(Pair(x, y))
    return a + b
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x + y, "astuple deconstruction did not behave as expected")

    @given(x=st.integers(), y=st.integers(), z=st.integers())
    def test_astuple_returns_tuple(self, x, y, z):
        source_code = """
from dataclasses import dataclass, astuple
from opshin.prelude import *

@dataclass
class Triple(PlutusData):
    CONSTR_ID = 0
    x: int
    y: int
    z: int

def validator(x: int, y: int, z: int) -> int:
    t = astuple(Triple(x, y, z))
    return t[0] + t[1] + t[2]
"""
        ret = eval_uplc_value(source_code, x, y, z)
        self.assertEqual(ret, x + y + z, "astuple did not return the expected tuple")

    @given(x=st.integers(), y=st.binary())
    def test_astuple_nested_plutusdata_fields(self, x, y):
        source_code = """
from dataclasses import dataclass, astuple
from opshin.prelude import *

@dataclass
class Left(PlutusData):
    CONSTR_ID = 0
    x: int

@dataclass
class Right(PlutusData):
    CONSTR_ID = 1
    y: bytes

@dataclass
class Pair(PlutusData):
    CONSTR_ID = 2
    left: Left
    right: Right

def validator(x: int, y: bytes) -> int:
    left, right = astuple(Pair(Left(x), Right(y)))
    return left.x + len(right.y)
"""
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(
            ret,
            x + len(y),
            "astuple did not preserve distinct nested PlutusData field types",
        )

    @given(a=st.integers(), b=st.binary())
    def test_validator_raw_tuple_input(self, a, b):
        source_code = """
from typing import Tuple

def validator(t: Tuple[int, bytes]) -> int:
    a, b = t
    return a + len(b)
"""
        ret = eval_uplc_value(source_code, (a, b))
        self.assertEqual(
            ret,
            a + len(b),
            "raw tuple validator input did not behave as expected",
        )

    def test_astuple_requires_import(self):
        source_code = """
from dataclasses import dataclass
from opshin.prelude import *

@dataclass
class Pair(PlutusData):
    CONSTR_ID = 0
    x: int
    y: int

def validator(x: int, y: int) -> int:
    a, b = astuple(Pair(x, y))
    return a + b
"""
        with self.assertRaises(CompilerError) as exc:
            builder._compile(source_code)
        self.assertIn("astuple must be imported", str(exc.exception).lower())

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
from typing import Dict, List, Union
def validator(xs: Dict[bytes, Dict[bytes, int]]) -> int:
    sum_values = 0
    for pid, tk_dict in xs.items():
        for tk_name, tk_amount in tk_dict.items():
            sum_values += tk_amount
    return sum_values
"""
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(
            ret,
            sum(v for pid, d in xs.items() for nam, v in d.items()),
            "for loop deconstruction did not behave as expected",
        )

    @given(xs=st.lists(st.tuples(st.integers(), st.integers()), max_size=10))
    def test_list_comprehension_tuple_deconstruction(self, xs):
        source_code = """
from typing import List

def validator(xs: List[List[int]]) -> List[int]:
    return [a + b for a, b in xs if a <= b]
"""
        list_xs = [list(pair) for pair in xs]
        ret = eval_uplc_value(source_code, list_xs)
        self.assertEqual(
            [x.value for x in ret],
            [a + b for a, b in xs if a <= b],
            "list comprehension deconstruction did not behave as expected",
        )

    @given(xs=st.dictionaries(st.integers(), st.integers(), max_size=10))
    def test_dict_comprehension_pair_deconstruction(self, xs):
        source_code = """
from typing import Dict

def validator(xs: Dict[int, int]) -> Dict[int, int]:
    return {k: v + 1 for k, v in xs.items() if k <= v}
"""
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(
            {k.value: v.value for k, v in ret.items()},
            {k: v + 1 for k, v in xs.items() if k <= v},
            "dict comprehension deconstruction did not behave as expected",
        )
