import pytest

from opshin import CompilerError
from opshin.type_impls import *
from tests.utils import eval_uplc_value


def test_record_type_order():
    A = RecordType(Record("A", "A", 0, [("foo", IntegerInstanceType)]))
    B = RecordType(Record("B", "B", 1, [("bar", IntegerInstanceType)]))
    C = RecordType(Record("C", "C", 2, [("baz", IntegerInstanceType)]))
    a = A
    b = B
    c = C

    assert a >= a
    assert not a >= b
    assert not b >= a
    assert not a >= c
    assert not c >= a
    assert not b >= c
    assert not c >= b

    A = RecordType(Record("A", "A", 0, [("foo", IntegerInstanceType)]))
    B = RecordType(
        Record(
            "B", "B", 0, [("foo", IntegerInstanceType), ("bar", IntegerInstanceType)]
        )
    )
    C = RecordType(Record("C", "C", 0, [("foo", InstanceType(AnyType()))]))
    assert not A >= B
    assert not C >= B
    assert C >= A


def test_union_type_order():
    A = RecordType(Record("A", "A", 0, [("foo", IntegerInstanceType)]))
    B = RecordType(Record("B", "B", 1, [("bar", IntegerInstanceType)]))
    C = RecordType(Record("C", "C", 2, [("baz", IntegerInstanceType)]))
    abc = UnionType([A, B, C])
    ab = UnionType([A, B])
    a = A
    c = C

    assert a >= a
    assert ab >= a
    assert not a >= ab
    assert abc >= ab
    assert not ab >= abc
    assert not c >= a
    assert not a >= c
    assert abc >= c
    assert not ab >= c


def test_tuple_size_order():
    A, B, C = IntegerInstanceType, IntegerInstanceType, IntegerInstanceType
    ab = TupleType([A, B])
    ac = TupleType([A, C])
    abc = TupleType([A, B, C])

    assert ab >= ab
    assert ac >= ac
    assert abc >= abc
    assert not abc >= ab
    assert not abc >= ac
    assert ab >= abc
    assert ac >= abc


def test_type_inference_list():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[int, bytes]) -> Union[int, bytes]:
    l = [x, 10, b"hello"]
    return l[1]
"""
    # primarily test that this does not fail to compile
    res = eval_uplc_value(source_code, 5)
    assert res == 10


def test_type_inference_list_2():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[int, bytes]) -> Union[int, bytes]:
    l = [10, x, b"hello"]
    return l[1]
"""
    # primarily test that this does not fail to compile
    res = eval_uplc_value(source_code, 5)
    assert res == 5


def test_type_inference_list_3():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: int) -> Union[int, bytes]:
    l = [10, b"hello"]
    return l[x]
"""
    # primarily test that this does not fail to compile
    res = eval_uplc_value(source_code, 0)
    assert res == 10
    res = eval_uplc_value(source_code, 1)
    assert res == b"hello"


def test_type_inference_dict():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[int, bytes]) -> Union[int, bytes]:
    l = {1: x, 2: 10, 3: b"hello"}
    return l[2]
"""
    # primarily test that this does not fail to compile
    res = eval_uplc_value(source_code, 5)
    assert res == 10


def test_type_inference_dict_2():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[int, bytes]) -> Union[int, bytes]:
    l = {1: 10, 2: x, 3: b"hello"}
    return l[1]
"""
    # primarily test that this does not fail to compile
    res = eval_uplc_value(source_code, 5)
    assert res == 10


def test_type_inference_dict_3():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[int, bytes]) -> Union[int, bytes]:
    l = {1: 10, x: 20, b"hi": 30}
    return l[1]
"""
    # primarily test that this does not fail to compile
    res = eval_uplc_value(source_code, 5)
    assert res == 10


def test_type_inference_dict_4():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[int, bytes]) -> Union[int, bytes]:
    l = {x: 10, 2: 20, b"hi": 30}
    return l[2]
"""
    # primarily test that this does not fail to compile
    res = eval_uplc_value(source_code, 5)
    assert res == 20


def test_type_inference_dict_5():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    foo: int

def validator(x: Union[int, bytes]) -> Union[int, bytes]:
    l = {x: 10, 2: 20, b"hi": 30}
    return l[x]
"""
    # primarily test that this does not fail to compile
    res = eval_uplc_value(source_code, 5)
    assert res == 10


def test_tuple_invalid_slice_type():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def validator(x: int) -> int:
    l = (x, 1)
    return l[0:1][0]
"""
    with pytest.raises(CompilerError):
        eval_uplc_value(source_code, 5)
