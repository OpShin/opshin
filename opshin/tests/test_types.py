from ..types import *


def test_union_type_order():
    A = RecordType(Record("A", "A", 0, [("foo", IntegerInstanceType)]))
    B = RecordType(Record("B", "B", 1, [("bar", IntegerInstanceType)]))
    C = RecordType(Record("C", "C", 2, [("baz", IntegerInstanceType)]))
    abc = UnionType([A, B, C])
    ab = UnionType([A, B])
    a = A

    assert a >= a
    assert ab >= a
    assert not a >= ab
    assert abc >= ab
    assert not ab >= abc
