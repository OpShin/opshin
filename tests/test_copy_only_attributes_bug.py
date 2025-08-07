import dataclasses
import unittest
from typing import List, Dict

from pycardano import PlutusData

from opshin import builder
from .utils import eval_uplc_value, Unit, eval_uplc


class TestCopyOnlyAttributesBug(unittest.TestCase):
    def test_nested_list_copy_only_attributes(self):
        """Test the bug report: ListType.copy_only_attributes() incorrectly converts items to/from data"""
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity
from dataclasses import dataclass

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    d: List[List[int]]

def validator(d: int) -> None:
    a: A = A([[d]])
    check_integrity(a)
    pass
"""
        # This should compile and run without error
        ret = eval_uplc_value(source_code, 42)
        self.assertIsNone(ret)

    def test_nested_dict_in_list_copy_only_attributes(self):
        """Test the bug report: Dicts nested in Lists also have the same issue"""
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity
from dataclasses import dataclass

@dataclass
class B(PlutusData):
    CONSTR_ID = 0
    d: List[Dict[int, str]]

def validator(d: int) -> None:
    b: B = B([{d: "test"}])
    check_integrity(b)
    pass
"""
        # This should compile and run without error
        ret = eval_uplc_value(source_code, 42)
        self.assertIsNone(ret)

    def test_dict_integrity(self):
        """Test the bug report: Dicts nested in Lists also have the same issue"""
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity
from dataclasses import dataclass
from typing import Dict, List, Union

@dataclass
class B(PlutusData):
    CONSTR_ID = 0
    d: List[Dict[int, bytes]]

def validator(d: Union[B, int]) -> None:
    check_integrity(d)
    pass
"""

        @dataclasses.dataclass
        class B(PlutusData):
            CONSTR_ID = 0
            d: List[Dict[int, bytes]]

        # This should compile and run without error
        eval_uplc(source_code, 42)
        eval_uplc(source_code, B([{42: b"test"}]))


if __name__ == "__main__":
    unittest.main()
