import unittest
import json
import cbor2
import typing
from dataclasses import dataclass
from typing import List, Dict, Union

import pycardano
from pycardano import PlutusData

from opshin.__main__ import plutus_data_from_json, plutus_data_from_cbor


@dataclass
class MockPlutusData(PlutusData):
    CONSTR_ID = 42
    value: int


@dataclass
class NestedPlutusData(PlutusData):
    CONSTR_ID = 123
    inner: MockPlutusData
    name: bytes


class TestPlutusDataFromJson(unittest.TestCase):

    def test_int_conversion(self):
        """Test conversion of integer from JSON"""
        json_data = {"int": 42}
        result = plutus_data_from_json(int, json_data)
        self.assertEqual(result, 42)

    def test_bytes_conversion(self):
        """Test conversion of bytes from JSON"""
        json_data = {"bytes": "48656c6c6f"}  # "Hello" in hex
        result = plutus_data_from_json(bytes, json_data)
        self.assertEqual(result, b"Hello")

    def test_none_conversion(self):
        """Test conversion of None"""
        json_data = {}  # None doesn't require specific JSON structure
        result = plutus_data_from_json(None, json_data)
        self.assertIsNone(result)

    def test_list_conversion(self):
        """Test conversion of List[int] from JSON"""
        json_data = {"list": [{"int": 1}, {"int": 2}, {"int": 3}]}
        result = plutus_data_from_json(List[int], json_data)
        self.assertEqual(result, [1, 2, 3])

    def test_nested_list_conversion(self):
        """Test conversion of nested lists from JSON"""
        json_data = {
            "list": [
                {"list": [{"int": 1}, {"int": 2}]},
                {"list": [{"int": 3}, {"int": 4}]},
            ]
        }
        result = plutus_data_from_json(List[List[int]], json_data)
        self.assertEqual(result, [[1, 2], [3, 4]])

    def test_dict_conversion(self):
        """Test conversion of Dict[int, bytes] from JSON"""
        json_data = {
            "map": [
                {"k": {"int": 1}, "v": {"bytes": "48656c6c6f"}},
                {"k": {"int": 2}, "v": {"bytes": "576f726c64"}},
            ]
        }
        result = plutus_data_from_json(Dict[int, bytes], json_data)
        expected = {1: b"Hello", 2: b"World"}
        self.assertEqual(result, expected)

    def test_union_conversion_int(self):
        """Test conversion of Union[int, bytes] matching int"""
        json_data = {"int": 42}
        result = plutus_data_from_json(Union[int, bytes], json_data)
        self.assertEqual(result, 42)

    def test_union_conversion_bytes(self):
        """Test conversion of Union[int, bytes] matching bytes"""
        # The union tries int first, fails, then should try bytes
        json_data = {"bytes": "48656c6c6f"}
        result = plutus_data_from_json(Union[int, bytes], json_data)
        self.assertEqual(result, b"Hello")

    def test_datum_int_conversion(self):
        """Test conversion of Datum containing int"""
        json_data = {"int": 123}
        result = plutus_data_from_json(pycardano.Datum, json_data)
        self.assertEqual(result, 123)

    def test_datum_bytes_conversion(self):
        """Test conversion of Datum containing bytes"""
        json_data = {"bytes": "48656c6c6f"}
        result = plutus_data_from_json(pycardano.Datum, json_data)
        self.assertEqual(result, b"Hello")

    def test_datum_list_conversion(self):
        """Test conversion of Datum containing list"""
        json_data = {"list": [{"int": 1}, {"int": 2}]}
        result = plutus_data_from_json(pycardano.Datum, json_data)
        self.assertEqual(result, [1, 2])

    def test_datum_map_conversion(self):
        """Test conversion of Datum containing map"""
        json_data = {"map": [{"k": {"int": 1}, "v": {"bytes": "48656c6c6f"}}]}
        result = plutus_data_from_json(pycardano.Datum, json_data)
        self.assertEqual(result, {1: b"Hello"})

    def test_plutus_data_subclass_conversion(self):
        """Test conversion of PlutusData subclass"""
        json_data = {"constructor": 42, "fields": [{"int": 100}]}

        # Mock the from_dict method for testing
        original_from_dict = MockPlutusData.from_dict
        MockPlutusData.from_dict = classmethod(lambda cls, d: MockPlutusData(value=100))

        try:
            result = plutus_data_from_json(MockPlutusData, json_data)
            self.assertIsInstance(result, MockPlutusData)
            self.assertEqual(result.value, 100)
        finally:
            MockPlutusData.from_dict = original_from_dict

    def test_invalid_annotation_error(self):
        """Test error handling for invalid annotation"""
        json_data = {"int": 42}
        # The function returns None for unhandled annotations
        result = plutus_data_from_json(str, json_data)
        self.assertIsNone(result)

    def test_missing_key_error(self):
        """Test error handling for missing key in JSON"""
        json_data = {"wrong_key": 42}
        with self.assertRaises(ValueError) as context:
            plutus_data_from_json(int, json_data)
        self.assertIn("does not match", str(context.exception))

    def test_union_no_match_error(self):
        """Test error handling when Union has no matching type"""
        json_data = {"constructor": 0, "fields": []}  # Constructor format
        with self.assertRaises(ValueError) as context:
            plutus_data_from_json(Union[int, bytes], json_data)
        self.assertIn("does not match", str(context.exception))


class TestPlutusDataFromCbor(unittest.TestCase):

    def test_int_conversion(self):
        """Test conversion of integer from CBOR"""
        cbor_data = cbor2.dumps(42)
        result = plutus_data_from_cbor(int, cbor_data)
        self.assertEqual(result, 42)

    def test_bytes_conversion(self):
        """Test conversion of bytes from CBOR"""
        test_bytes = b"Hello World"
        cbor_data = cbor2.dumps(test_bytes)
        result = plutus_data_from_cbor(bytes, cbor_data)
        self.assertEqual(result, test_bytes)

    def test_none_conversion(self):
        """Test conversion of None"""
        cbor_data = cbor2.dumps(None)
        result = plutus_data_from_cbor(None, cbor_data)
        self.assertIsNone(result)

    def test_none_conversion_incorrect(self):
        """Test conversion of None"""
        cbor_data = cbor2.dumps(1)
        with self.assertRaises(ValueError) as context:
            plutus_data_from_cbor(None, cbor_data)
        self.assertIn("does not match", str(context.exception))

    def test_list_conversion(self):
        """Test conversion of List[int] from CBOR"""
        test_list = [1, 2, 3, 4]
        cbor_data = cbor2.dumps(test_list)
        result = plutus_data_from_cbor(List[int], cbor_data)
        self.assertEqual(result, test_list)

    def test_nested_list_conversion(self):
        """Test conversion of nested lists from CBOR"""
        test_list = [[1, 2], [3, 4], [5, 6]]
        cbor_data = cbor2.dumps(test_list)
        result = plutus_data_from_cbor(List[List[int]], cbor_data)
        self.assertEqual(result, test_list)

    def test_dict_conversion(self):
        """Test conversion of Dict[int, bytes] from CBOR"""
        test_dict = {1: b"Hello", 2: b"World", 3: b"Test"}
        cbor_data = cbor2.dumps(test_dict)
        result = plutus_data_from_cbor(Dict[int, bytes], cbor_data)
        self.assertEqual(result, test_dict)

    def test_union_conversion_int(self):
        """Test conversion of Union[int, bytes] matching int"""
        cbor_data = cbor2.dumps(42)
        result = plutus_data_from_cbor(Union[int, bytes], cbor_data)
        self.assertEqual(result, 42)

    def test_union_conversion_bytes(self):
        """Test conversion of Union[int, bytes] matching bytes"""
        test_bytes = b"Hello"
        cbor_data = cbor2.dumps(test_bytes)
        result = plutus_data_from_cbor(Union[int, bytes], cbor_data)
        self.assertEqual(result, test_bytes)

    def test_plutus_data_subclass_conversion(self):
        """Test conversion of PlutusData subclass from CBOR"""
        # Create mock CBOR data for a PlutusData instance
        test_cbor = b"\x82\x18*\x81\x18d"  # CBOR for constructor 42 with field [100]

        # Mock the from_cbor method for testing
        original_from_cbor = MockPlutusData.from_cbor
        MockPlutusData.from_cbor = classmethod(
            lambda cls, cbor: MockPlutusData(value=100)
        )

        try:
            result = plutus_data_from_cbor(MockPlutusData, test_cbor)
            self.assertIsInstance(result, MockPlutusData)
            self.assertEqual(result.value, 100)
        finally:
            MockPlutusData.from_cbor = original_from_cbor

    def test_invalid_annotation_error(self):
        """Test error handling for invalid annotation"""
        cbor_data = cbor2.dumps(42)
        # The function returns None for unhandled annotations
        result = plutus_data_from_cbor(str, cbor_data)
        self.assertIsNone(result)

    def test_invalid_cbor_data(self):
        """Test error handling for invalid CBOR data"""
        invalid_cbor = b"\xff\xff\xff"  # Invalid CBOR
        with self.assertRaises(ValueError) as context:
            plutus_data_from_cbor(int, invalid_cbor)
        self.assertIn("does not match", str(context.exception))

    def test_union_no_match_error(self):
        """Test error handling when Union has no matching type"""
        # Create CBOR data that doesn't match int or bytes (e.g., a list)
        cbor_data = cbor2.dumps([1, 2, 3])
        with self.assertRaises(ValueError) as context:
            plutus_data_from_cbor(Union[int, bytes], cbor_data)
        self.assertIn("does not match", str(context.exception))

    def test_complex_nested_structure(self):
        """Test conversion of complex nested structure"""
        test_data = {1: [10, 20, 30], 2: [40, 50, 60], 3: [70, 80, 90]}
        cbor_data = cbor2.dumps(test_data)
        result = plutus_data_from_cbor(Dict[int, List[int]], cbor_data)
        self.assertEqual(result, test_data)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for both functions"""

    def test_empty_list_json(self):
        """Test empty list conversion from JSON"""
        json_data = {"list": []}
        result = plutus_data_from_json(List[int], json_data)
        self.assertEqual(result, [])

    def test_empty_list_cbor(self):
        """Test empty list conversion from CBOR"""
        cbor_data = cbor2.dumps([])
        result = plutus_data_from_cbor(List[int], cbor_data)
        self.assertEqual(result, [])

    def test_empty_dict_json(self):
        """Test empty dict conversion from JSON"""
        json_data = {"map": []}
        result = plutus_data_from_json(Dict[int, str], json_data)
        self.assertEqual(result, {})

    def test_empty_dict_cbor(self):
        """Test empty dict conversion from CBOR"""
        cbor_data = cbor2.dumps({})
        result = plutus_data_from_cbor(Dict[int, bytes], cbor_data)
        self.assertEqual(result, {})

    def test_large_integers(self):
        """Test large integer handling"""
        large_int = 2**63 - 1  # Large but valid integer

        # JSON test
        json_data = {"int": large_int}
        result_json = plutus_data_from_json(int, json_data)
        self.assertEqual(result_json, large_int)

        # CBOR test
        cbor_data = cbor2.dumps(large_int)
        result_cbor = plutus_data_from_cbor(int, cbor_data)
        self.assertEqual(result_cbor, large_int)

    def test_zero_values(self):
        """Test zero integer handling"""
        # JSON test
        json_data = {"int": 0}
        result_json = plutus_data_from_json(int, json_data)
        self.assertEqual(result_json, 0)

        # CBOR test
        cbor_data = cbor2.dumps(0)
        result_cbor = plutus_data_from_cbor(int, cbor_data)
        self.assertEqual(result_cbor, 0)

    def test_negative_integers(self):
        """Test negative integer handling"""
        # JSON test
        json_data = {"int": -42}
        result_json = plutus_data_from_json(int, json_data)
        self.assertEqual(result_json, -42)

        # CBOR test
        cbor_data = cbor2.dumps(-42)
        result_cbor = plutus_data_from_cbor(int, cbor_data)
        self.assertEqual(result_cbor, -42)

    def test_empty_bytes(self):
        """Test empty bytes handling"""
        # JSON test
        json_data = {"bytes": ""}
        result_json = plutus_data_from_json(bytes, json_data)
        self.assertEqual(result_json, b"")

        # CBOR test
        cbor_data = cbor2.dumps(b"")
        result_cbor = plutus_data_from_cbor(bytes, cbor_data)
        self.assertEqual(result_cbor, b"")


if __name__ == "__main__":
    unittest.main()
