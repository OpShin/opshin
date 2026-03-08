import unittest

from hypothesis import given
from hypothesis import strategies as st

from opshin import builder
from opshin.util import CompilerError
from tests.utils import eval_uplc_value, Unit


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
