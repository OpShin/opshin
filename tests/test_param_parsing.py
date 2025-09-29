import unittest
import json
import typing
from typing import List, Dict, Union

import pycardano
from pycardano import PlutusData
from dataclasses import dataclass

from uplc.ast import PlutusInteger, PlutusByteString, PlutusList, PlutusMap

from opshin.__main__ import parse_uplc_param, parse_plutus_param


@dataclass
class MockPlutusDataForParams(PlutusData):
    CONSTR_ID = 42
    value: int


class TestParseUplcParam(unittest.TestCase):
    """Test cases for parse_uplc_param function"""

    def test_parse_json_dict_valid(self):
        """Test parsing valid JSON dictionary"""
        param = '{"int": 42}'
        result = parse_uplc_param(param)
        # The result should be a PlutusInteger with value 42
        self.assertEqual(result, PlutusInteger(42))

    def test_parse_json_dict_complex(self):
        """Test parsing complex JSON structure"""
        param = '{"list": [{"int": 1}, {"int": 2}]}'
        result = parse_uplc_param(param)
        # Should be a PlutusList containing two PlutusIntegers
        from frozenlist import FrozenList

        expected = PlutusList(FrozenList([PlutusInteger(1), PlutusInteger(2)]))
        self.assertEqual(result, expected)

    def test_parse_json_dict_nested(self):
        """Test parsing nested JSON structure"""
        param = '{"map": [{"k": {"int": 1}, "v": {"bytes": "48656c6c6f"}}]}'
        result = parse_uplc_param(param)
        # Should be a PlutusMap with one entry: PlutusInteger(1) -> PlutusByteString(b"Hello")
        import frozendict

        expected = PlutusMap(
            frozendict.frozendict({PlutusInteger(1): PlutusByteString(b"Hello")})
        )
        self.assertEqual(result, expected)

    def test_parse_hex_cbor_valid(self):
        """Test parsing valid hex-encoded CBOR"""
        param = "182a"  # CBOR encoding of integer 42
        result = parse_uplc_param(param)
        # Should be a PlutusInteger with value 42
        self.assertEqual(result, PlutusInteger(42))

    def test_parse_hex_cbor_bytes(self):
        """Test parsing hex-encoded CBOR bytes"""
        param = "4568656c6c6f"  # CBOR encoding of bytes "hello" (correct hex)
        result = parse_uplc_param(param)
        # Should be a PlutusByteString with value b"hello"
        self.assertEqual(result, PlutusByteString(b"hello"))

    def test_parse_hex_cbor_list(self):
        """Test parsing hex-encoded CBOR list"""
        param = "83010203"  # CBOR encoding of [1, 2, 3]
        result = parse_uplc_param(param)
        # Should be a PlutusList containing three PlutusIntegers
        from frozenlist import FrozenList

        expected = PlutusList(
            FrozenList([PlutusInteger(1), PlutusInteger(2), PlutusInteger(3)])
        )
        self.assertEqual(result, expected)

    def test_invalid_json_format(self):
        """Test error handling for invalid JSON format"""
        param = '{"int": 42'  # Missing closing brace
        with self.assertRaises(ValueError) as context:
            parse_uplc_param(param)
        self.assertIn("Invalid parameter", str(context.exception))
        self.assertIn("expected JSON value", str(context.exception))

    def test_invalid_json_syntax(self):
        """Test error handling for invalid JSON syntax"""
        param = '{"int": }'  # Invalid JSON syntax
        with self.assertRaises(ValueError) as context:
            parse_uplc_param(param)
        self.assertIn("Invalid parameter", str(context.exception))

    def test_invalid_hex_string(self):
        """Test error handling for invalid hex string"""
        param = "xyz123"  # Invalid hex characters
        with self.assertRaises(ValueError) as context:
            parse_uplc_param(param)
        self.assertIn("Expected hexadecimal CBOR", str(context.exception))
        self.assertIn("could not transform hex string to bytes", str(context.exception))

    def test_invalid_hex_odd_length(self):
        """Test error handling for odd-length hex string"""
        param = "1234f"  # Odd number of hex digits
        with self.assertRaises(ValueError) as context:
            parse_uplc_param(param)
        self.assertIn("Expected hexadecimal CBOR", str(context.exception))

    def test_invalid_cbor_data(self):
        """Test error handling for invalid CBOR data"""
        param = "ff"  # Valid hex but invalid CBOR
        with self.assertRaises(ValueError) as context:
            parse_uplc_param(param)
        self.assertIn("Expected hexadecimal CBOR", str(context.exception))

    def test_empty_string(self):
        """Test error handling for empty string"""
        param = ""
        with self.assertRaises(ValueError) as context:
            parse_uplc_param(param)
        self.assertIn("could not transform hex string to bytes", str(context.exception))

    def test_whitespace_only(self):
        """Test error handling for whitespace-only string"""
        param = "   "
        with self.assertRaises(ValueError) as context:
            parse_uplc_param(param)
        self.assertIn("could not transform hex string to bytes", str(context.exception))


class TestParsePlutusParam(unittest.TestCase):
    """Test cases for parse_plutus_param function"""

    def test_parse_json_int(self):
        """Test parsing JSON integer parameter"""
        param = '{"int": 42}'
        result = parse_plutus_param(int, param)
        self.assertEqual(result, 42)

    def test_parse_json_bytes(self):
        """Test parsing JSON bytes parameter"""
        param = '{"bytes": "48656c6c6f"}'  # "Hello" in hex
        result = parse_plutus_param(bytes, param)
        self.assertEqual(result, b"Hello")

    def test_parse_json_list(self):
        """Test parsing JSON list parameter"""
        param = '{"list": [{"int": 1}, {"int": 2}, {"int": 3}]}'
        result = parse_plutus_param(List[int], param)
        self.assertEqual(result, [1, 2, 3])

    def test_parse_json_dict(self):
        """Test parsing JSON dictionary parameter"""
        param = '{"map": [{"k": {"int": 1}, "v": {"bytes": "48656c6c6f"}}]}'
        result = parse_plutus_param(Dict[int, bytes], param)
        expected = {1: b"Hello"}
        self.assertEqual(result, expected)

    def test_parse_cbor_int(self):
        """Test parsing CBOR integer parameter"""
        param = "182a"  # CBOR encoding of integer 42
        result = parse_plutus_param(int, param)
        self.assertEqual(result, 42)

    def test_parse_cbor_bytes(self):
        """Test parsing CBOR bytes parameter"""
        param = "4568656c6c6f"  # CBOR encoding of bytes "hello" (correct hex)
        result = parse_plutus_param(bytes, param)
        self.assertEqual(result, b"hello")

    def test_parse_cbor_list(self):
        """Test parsing CBOR list parameter"""
        param = "83010203"  # CBOR encoding of [1, 2, 3]
        result = parse_plutus_param(List[int], param)
        self.assertEqual(result, [1, 2, 3])

    def test_parse_union_type_int(self):
        """Test parsing Union type matching int"""
        param = '{"int": 42}'
        result = parse_plutus_param(Union[int, bytes], param)
        self.assertEqual(result, 42)

    def test_parse_union_type_bytes(self):
        """Test parsing Union type matching bytes"""
        param = "4568656c6c6f"  # CBOR bytes (correct hex)
        result = parse_plutus_param(Union[int, bytes], param)
        self.assertEqual(result, b"hello")

    def test_parse_none_type(self):
        """Test parsing None type"""
        param = '{"constructor": 0, "fields": []}'
        result = parse_plutus_param(None, param)
        self.assertIsNone(result)

    def test_invalid_json_format_error(self):
        """Test error handling for invalid JSON format"""
        param = '{"int": 42'  # Missing closing brace
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(int, param)
        self.assertIn("Invalid parameter", str(context.exception))

    def test_invalid_hex_format_error(self):
        """Test error handling for invalid hex format"""
        param = "xyz123"  # Invalid hex
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(int, param)
        self.assertIn("Expected hexadecimal CBOR", str(context.exception))

    def test_type_mismatch_json(self):
        """Test error handling for type mismatch with JSON"""
        param = '{"bytes": "48656c6c6f"}'  # bytes format
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(int, param)  # expecting int
        self.assertIn("does not match", str(context.exception))

    def test_type_mismatch_cbor(self):
        """Test error handling for type mismatch with CBOR"""
        param = "zzhello"  # Invalid hex
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(int, param)  # expecting int
        self.assertIn("could not transform hex string to bytes", str(context.exception))

    def test_invalid_json_structure(self):
        """Test error handling for invalid JSON structure"""
        param = '{"wrong_key": 42}'
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(int, param)
        self.assertIn("does not match", str(context.exception))

    def test_empty_json_object(self):
        """Test handling of empty JSON object"""
        param = "{}"
        # This should work for None type
        result = parse_plutus_param(None, param)
        self.assertIsNone(result)

    def test_complex_nested_structure(self):
        """Test parsing complex nested structure"""
        param = (
            '{"map": [{"k": {"int": 1}, "v": {"list": [{"int": 10}, {"int": 20}]}}]}'
        )
        result = parse_plutus_param(Dict[int, List[int]], param)
        expected = {1: [10, 20]}
        self.assertEqual(result, expected)

    def test_large_integer_values(self):
        """Test parsing large integer values"""
        large_int = 2**63 - 1
        param = f'{{"int": {large_int}}}'
        result = parse_plutus_param(int, param)
        self.assertEqual(result, large_int)

    def test_negative_integer_values(self):
        """Test parsing negative integer values"""
        param = '{"int": -42}'
        result = parse_plutus_param(int, param)
        self.assertEqual(result, -42)

    def test_zero_values(self):
        """Test parsing zero values"""
        param = '{"int": 0}'
        result = parse_plutus_param(int, param)
        self.assertEqual(result, 0)

    def test_empty_bytes(self):
        """Test parsing empty bytes"""
        param = '{"bytes": ""}'
        result = parse_plutus_param(bytes, param)
        self.assertEqual(result, b"")

    def test_empty_list(self):
        """Test parsing empty list"""
        param = '{"list": []}'
        result = parse_plutus_param(List[int], param)
        self.assertEqual(result, [])

    def test_empty_dict(self):
        """Test parsing empty dictionary"""
        param = '{"map": []}'
        result = parse_plutus_param(Dict[int, str], param)
        self.assertEqual(result, {})

    def test_malformed_cbor(self):
        """Test error handling for malformed CBOR"""
        param = "ff"  # Invalid CBOR
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(int, param)
        # Should raise an error when trying to parse invalid CBOR

    def test_unsupported_annotation_type(self):
        """Test handling of unsupported annotation type"""
        param = '{"int": 42}'
        result = parse_plutus_param(str, param)  # str is not directly supported
        # The function should return None for unsupported types
        self.assertIsNone(result)


class TestEdgeCasesAndCornerCases(unittest.TestCase):
    """Test edge cases and corner cases for both functions"""

    def test_very_long_hex_string(self):
        """Test handling of very long hex strings"""
        # Create a long but valid hex string (100 bytes of zeros)
        param = "00" * 100
        result = parse_uplc_param(param)
        # Should be a PlutusInteger with value 0
        self.assertEqual(result, PlutusInteger(0))

    def test_unicode_in_json(self):
        """Test handling of Unicode characters in JSON"""
        param = '{"bytes": "48656c6c6f"}'  # Valid JSON encoding bytes "Hello"
        result = parse_uplc_param(param)
        # Should be a PlutusByteString with value b"Hello"
        self.assertEqual(result, PlutusByteString(b"Hello"))

    def test_deeply_nested_json(self):
        """Test handling of deeply nested JSON structures"""
        param = '{"list": [{"list": [{"list": [{"int": 42}]}]}]}'
        result = parse_uplc_param(param)
        # Should be a deeply nested PlutusList structure
        from frozenlist import FrozenList

        expected = PlutusList(
            FrozenList(
                [PlutusList(FrozenList([PlutusList(FrozenList([PlutusInteger(42)]))]))]
            )
        )
        self.assertEqual(result, expected)

    def test_mixed_case_hex(self):
        """Test handling of mixed case hex strings"""
        param = "182A"  # Mixed case hex
        result = parse_uplc_param(param)
        self.assertEqual(result, PlutusInteger(42))

    def test_hex_with_spaces(self):
        """Test that hex with spaces fails appropriately"""
        param = "18 2a"  # Hex with space
        res = parse_uplc_param(param)
        self.assertEqual(
            res, PlutusInteger(42)
        )  # Should parse correctly ignoring spaces

    def test_json_with_extra_whitespace(self):
        """Test JSON with extra whitespace that doesn't start with {"""
        param = '{  "int" : 42  }'  # JSON that starts with { (no leading space)
        result = parse_uplc_param(param)
        self.assertEqual(result, PlutusInteger(42))

    def test_cbor_vs_json_disambiguation(self):
        """Test that CBOR vs JSON is correctly disambiguated"""
        # JSON format (starts with {)
        json_param = '{"int": 42}'
        json_result = parse_uplc_param(json_param)

        # CBOR format (hex string)
        cbor_param = "182a"  # 42 in CBOR
        cbor_result = parse_uplc_param(cbor_param)

        # Both should return PlutusInteger(42) and be equal
        expected = PlutusInteger(42)
        self.assertEqual(json_result, expected)
        self.assertEqual(cbor_result, expected)
        # They should be equal to each other
        self.assertEqual(json_result, cbor_result)

    def test_invalid_json(self):
        """Test parsing JSON integer parameter"""
        param = '"int": 42}'
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(int, param)
        self.assertIn("Could not parse", str(context.exception))
        param = "0P"
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(int, param)
        self.assertIn("Could not parse", str(context.exception))
        param = '{"int": 42}'
        with self.assertRaises(ValueError) as context:
            parse_plutus_param(List[int], param)
        self.assertIn("Could not parse", str(context.exception))


if __name__ == "__main__":
    unittest.main()
