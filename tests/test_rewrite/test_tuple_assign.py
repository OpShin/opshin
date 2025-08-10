import unittest

from opshin import builder, CompilerError


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
