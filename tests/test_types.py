from opshin.type_impls import *


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
