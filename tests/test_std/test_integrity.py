from parameterized import parameterized
import dataclasses
import unittest
from typing import List, Dict

from pycardano import PlutusData

from uplc import ast as uplc, eval as uplc_eval
from ..utils import eval_uplc


@parameterized.expand(
    [
        [[0, 1]],
        [[0]],
        [[0, 1, 2]],
        [[b"hello", 0]],
    ]
)
def test_integrity_check(xs):
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: B) -> None:
    check_integrity(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [
            uplc.PlutusInteger(x) if isinstance(x, int) else uplc.PlutusByteString(x)
            for x in xs
        ],
    )
    try:
        eval_uplc(source_code, obj)
    except Exception as e:
        print(e)
        res = False
    else:
        res = True
    assert res == (len(xs) == 2 and all(isinstance(x, int) for x in xs))


@parameterized.expand(
    [
        [0],
        [1],
        [2],
    ]
)
def test_integrity_check_list(bar_constr):
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass()
class A(PlutusData):
    CONSTR_ID = 1
    
@dataclass()
class C(PlutusData):
    CONSTR_ID = 0

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    bar: Union[A, C]

def validator(x: B) -> None:
    check_integrity(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [uplc.PlutusConstr(bar_constr, [])],
    )
    try:
        eval_uplc(source_code, obj)
    except:
        res = False
    else:
        res = True
    assert res == (bar_constr in (0, 1))


@parameterized.expand(
    [
        [[0, 1], [1, 1, 1]],
        [[b"hello"], [1, 1]],
        [[0, 1, 2], [1, 0]],
    ]
)
def test_integrity_check_list(foobar, bar_constrs):
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass()
class A(PlutusData):
    CONSTR_ID = 1

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: List[int]
    bar: List[A]

def validator(x: B) -> None:
    check_integrity(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [
            uplc.PlutusList(
                [
                    (
                        uplc.PlutusInteger(x)
                        if isinstance(x, int)
                        else uplc.PlutusByteString(x)
                    )
                    for x in foobar
                ]
            ),
            uplc.PlutusList([uplc.PlutusConstr(c, []) for c in bar_constrs]),
        ],
    )
    try:
        eval_uplc(source_code, obj)
    except:
        res = False
    else:
        res = True
    assert res == (
        all(isinstance(x, int) for x in foobar) and all(c == 1 for c in bar_constrs)
    )


@parameterized.expand(
    [
        [[0, 1, 2], [1, 1, 1]],
        # check for incorrect type in keys
        [[b"hello", 1], [1, 1]],
        # check for incorrect type in values
        [[1, 2], [1, b"hello"]],
    ]
)
def test_integrity_check_dict(keys, values):
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: Dict[int, int]

def validator(x: B) -> None:
    check_integrity(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [
            uplc.PlutusMap(
                {
                    (
                        uplc.PlutusInteger(x)
                        if isinstance(x, int)
                        else uplc.PlutusByteString(x)
                    ): (
                        uplc.PlutusInteger(y)
                        if isinstance(y, int)
                        else uplc.PlutusByteString(y)
                    )
                    for x, y in zip(keys, values)
                },
            ),
        ],
    )
    try:
        eval_uplc(source_code, obj)
    except:
        res = False
    else:
        res = True
    assert res == (
        all(isinstance(x, int) for x in keys + values) and len(set(keys)) == len(keys)
    )


def test_integrity_check_rename():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity as integ

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int

def validator(x: B) -> None:
    integ(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [uplc.PlutusInteger(1)],
    )
    eval_uplc(source_code, obj)


class TestCopyOnlyAttributesBug(unittest.TestCase):

    def test_int_copy_only_attributes(self):
        """Test the bug report: ListType.copy_only_attributes() incorrectly converts items to/from data"""
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity
from dataclasses import dataclass

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    d: int

def validator(d: int) -> None:
    a: A = A(d)
    check_integrity(a)
    pass
    """
        # This should compile and run without error
        eval_uplc(source_code, 42)

    def test_wrong_data_copy_only_attributes(self):
        """Test the bug report: ListType.copy_only_attributes() incorrectly converts items to/from data"""
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity
from dataclasses import dataclass

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    d: int

def validator(d: A) -> None:
    check_integrity(d)
    pass
    """

        @dataclasses.dataclass
        class A(PlutusData):
            CONSTR_ID = 0
            d: bytes

        try:
            eval_uplc(source_code, A(b"test"))
        except Exception as e:
            assert isinstance(
                e, RuntimeError
            ), "Expected a RuntimeError for invalid type"

    def test_wrong_constructor_copy_only_attributes(self):
        """Test the bug report: ListType.copy_only_attributes() incorrectly converts items to/from data"""
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity
from dataclasses import dataclass

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    d: int

def validator(d: A) -> None:
    check_integrity(d)
    pass
    """

        @dataclasses.dataclass
        class A(PlutusData):
            CONSTR_ID = 1
            d: int

        try:
            eval_uplc(source_code, A(42))
            self.fail("Expected a RuntimeError for invalid type")
        except Exception as e:
            assert isinstance(
                e, RuntimeError
            ), "Expected a RuntimeError for invalid type"

    def test_list_int_copy_only_attributes(self):
        """Test the bug report: ListType.copy_only_attributes() incorrectly converts items to/from data"""
        source_code = """
from opshin.prelude import *
from opshin.std.integrity import check_integrity
from dataclasses import dataclass

@dataclass
class A(PlutusData):
    CONSTR_ID = 0
    d: List[int]

def validator(d: int) -> None:
    a: A = A([d, d+1])
    check_integrity(a)
    pass
    """
        # This should compile and run without error
        eval_uplc(source_code, 42)

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
        eval_uplc(source_code, 42)

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
        eval_uplc(source_code, 42)

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

        @dataclasses.dataclass
        class A(PlutusData):
            CONSTR_ID = 2
            d: int

        # This should compile and run without error
        eval_uplc(source_code, 42)
        eval_uplc(source_code, B([{42: b"test"}]))
        try:
            eval_uplc(source_code, b"test")
        except Exception as e:
            assert isinstance(
                e, RuntimeError
            ), "Expected a RuntimeError for invalid type"
        try:
            eval_uplc(source_code, A(42))
        except Exception as e:
            assert isinstance(
                e, RuntimeError
            ), "Expected a RuntimeError for invalid type"

    def test_union_integrity(self):
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

@dataclass
class A(PlutusData):
    CONSTR_ID = 2
    d: int

def validator(d: Union[A, B, List[Anything], Dict[Anything,Anything], int, bytes]) -> None:
    check_integrity(d)
    pass
"""

        @dataclasses.dataclass
        class B(PlutusData):
            CONSTR_ID = 0
            d: List[Dict[int, bytes]]

        @dataclasses.dataclass
        class A(PlutusData):
            CONSTR_ID = 2
            d: int

        # This should compile and run without error
        eval_uplc(source_code, 42)
        eval_uplc(source_code, B([{42: b"test"}]))
        eval_uplc(source_code, A(42))
        eval_uplc(source_code, b"test")
        eval_uplc(source_code, [42, 43, 44])
        eval_uplc(source_code, {42: b"test", 43: b"test2"})


if __name__ == "__main__":
    unittest.main()
