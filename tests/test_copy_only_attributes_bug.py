import unittest
from opshin import builder
from .utils import eval_uplc_value, Unit


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


if __name__ == "__main__":
    unittest.main()
