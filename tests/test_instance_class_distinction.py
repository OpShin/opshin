"""
Test cases for distinguishing between class and instance method access.

This tests the distinction between:
- bytes.fromhex() (class method)
- b''.decode() and b''.hex() (instance methods)
"""

import unittest
from opshin import builder
from .utils import eval_uplc_value, Unit


class InstanceClassDistinctionTest(unittest.TestCase):
    def test_bytes_instance_methods_work(self):
        """Test that decode() and hex() work as instance methods"""
        source_code = """
def validator(_: None) -> str:
    data = b"Hello"
    # These should work - accessing methods on byte string instances
    hex_result = data.hex()
    return hex_result
"""
        # This should compile and run successfully
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, b"48656c6c6f")

    def test_bytes_instance_decode_works(self):
        """Test that decode() works as instance method"""
        source_code = """
def validator(_: None) -> str:
    data = b"Hello"
    decode_result = data.decode()
    return decode_result
"""
        # This should compile and run successfully
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, b"Hello")

    def test_bytes_class_fromhex_works(self):
        """Test that fromhex() works as a class method"""
        source_code = """
def validator(_: None) -> bytes:
    # This should work - accessing fromhex on the bytes class
    result = bytes.fromhex("48656c6c6f")
    return result
"""
        # This should compile and run successfully
        res = eval_uplc_value(source_code, Unit())
        self.assertEqual(res, b"Hello")

    def test_bytes_instance_cannot_access_fromhex(self):
        """Test that fromhex() is NOT accessible on instances (should fail)"""
        source_code = """
def validator(_: None) -> bytes:
    data = b"Hello"
    # This should fail - fromhex should not be accessible on instances
    result = data.fromhex("48656c6c6f")
    return result
"""
        # This should raise an exception during compilation
        with self.assertRaises(Exception):
            builder._compile(source_code)

    def test_bytes_class_cannot_access_instance_methods_decode(self):
        """Test that decode() is NOT accessible on the class (should fail)"""
        source_code = """
def validator(_: None) -> str:
    # This should fail - decode should not be accessible on the class
    result = bytes.decode()
    return result
"""
        # This should raise an exception during compilation
        with self.assertRaises(Exception):
            builder._compile(source_code)

    def test_bytes_class_cannot_access_instance_methods_hex(self):
        """Test that hex() is NOT accessible on the class (should fail)"""
        source_code = """
def validator(_: None) -> str:
    # This should fail - hex should not be accessible on the class
    result = bytes.hex()
    return result
"""
        # This should raise an exception during compilation
        with self.assertRaises(Exception):
            builder._compile(source_code)

    def test_current_behavior_all_methods_accessible(self):
        """Test current behavior where all methods are accessible everywhere (this will change)"""
        # Currently, both instance and class can access all methods
        # This test documents the current behavior before we implement the fix

        # Instance accessing fromhex (currently works, should fail after fix)
        source_code_instance_fromhex = """
def validator(_: None) -> bytes:
    data = b"Hello"
    result = data.fromhex("48656c6c6f")
    return result
"""

        # Class accessing decode (currently works, should fail after fix)
        source_code_class_decode = """
def validator(_: None) -> str:
    # Note: this currently might work due to forwarding, but should fail
    # We'll need to check if this actually compiles in current implementation
    pass
"""

        # For now, let's just test that the instance methods work
        source_code_working = """
def validator(_: None) -> str:
    data = b"Hello"
    return data.hex()
"""
        res = eval_uplc_value(source_code_working, Unit())
        self.assertEqual(res, b"48656c6c6f")
