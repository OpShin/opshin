from typing import Tuple, List

import hypothesis
import hypothesis.strategies as hst

from opshin import builder
from opshin.std import bitmap as oc_bitmap


@hypothesis.given(hst.integers(min_value=0, max_value=1000))
def test_init_bitmap(x: int):
    assert (
        len(oc_bitmap.init_bitmap(x)) * 8 >= x
    ), "Insufficient size of initialized bitmap"


@hst.composite
def bytes_and_index(draw):
    xs = draw(hst.binary(min_size=1))
    i = draw(hst.integers(min_value=0, max_value=len(xs)))
    return (xs, i)


@hst.composite
def bytes_and_indices(draw):
    xs = draw(hst.binary(min_size=1))
    i = draw(
        hst.lists(hst.integers(min_value=0, max_value=len(xs)), min_size=1, max_size=10)
    )
    return (xs, i)


@hypothesis.given(bytes_and_index())
@hypothesis.example((b"\x01", 0))
def test_test_bitmap(p: Tuple[bytes, int]):
    a, i = p
    ith_bit = int.from_bytes(a, "big") & (1 << i)
    assert oc_bitmap.test_bitmap(a, i) == (ith_bit != 0), "Invalid isset check"


@hypothesis.given(bytes_and_indices())
def test_set_bitmap(p: Tuple[bytes, List[int]]):
    a, i_list = p
    set_bit = int.from_bytes(a, "big")
    for i in i_list:
        set_bit = set_bit | (1 << i)
    set_bit = set_bit.to_bytes(len(a), byteorder="big")
    assert oc_bitmap.set_bitmap(a, i_list) == set_bit, "Set bit incorrectly"


@hypothesis.given(bytes_and_indices())
def test_reset_bitmap(p: Tuple[bytes, List[int]]):
    a, i_list = p
    set_bit = int.from_bytes(a, "big")
    for i in i_list:
        set_bit = set_bit & (~(1 << i))
    set_bit = set_bit.to_bytes(len(a), byteorder="big")
    assert oc_bitmap.reset_bitmap(a, i_list) == set_bit, "Reset bit incorrectly"


@hypothesis.given(bytes_and_index())
def test_flip_bitmap(p: Tuple[bytes, int]):
    a, i = p
    set_bit = int.from_bytes(a, "big") ^ (1 << i)
    set_bit = set_bit.to_bytes(len(a), byteorder="big")
    assert oc_bitmap.flip_bitmap(a, i) == set_bit, "Flipped bit incorrectly"


@hypothesis.given(hst.binary())
def test_size_bitmap(x: bytes):
    assert len(x) * 8 == oc_bitmap.size_bitmap(x), "Incorrect size of bitmap"


@hypothesis.given(hst.binary())
def test_all_bitmap(x: bytes):
    assert oc_bitmap.all_bitmap(x) == all(
        b == 0xFF for b in x
    ), "All is incorrect for bitmap"


@hypothesis.given(hst.binary())
def test_any_bitmap(x: bytes):
    assert oc_bitmap.any_bitmap(x) == any(
        b != 0x00 for b in x
    ), "Any is incorrect for bitmap"


@hypothesis.given(hst.binary())
def test_none_bitmap(x: bytes):
    assert oc_bitmap.none_bitmap(x) == all(
        b == 0x00 for b in x
    ), "None is incorrect for bitmap"


@hypothesis.given(bytes_and_index())
def test_flip_roundtrip(p: Tuple[bytes, int]):
    a, i = p
    assert (
        oc_bitmap.flip_bitmap(oc_bitmap.flip_bitmap(a, i), i) == a
    ), "Flipped bit incorrectly"


@hypothesis.given(bytes_and_index())
def test_set_test(p: Tuple[bytes, int]):
    a, i = p
    assert oc_bitmap.test_bitmap(oc_bitmap.set_bitmap(a, [i]), i), "Set bit incorrectly"


@hypothesis.given(bytes_and_index())
def test_reset_test(p: Tuple[bytes, int]):
    a, i = p
    assert not oc_bitmap.test_bitmap(
        oc_bitmap.reset_bitmap(a, [i]), i
    ), "Reset bit incorrectly"


def test_compile():
    source_code = """
from opshin.std.bitmap import *
from typing import Dict, List, Union

def validator(a: int, b:int, c: int) -> int:
    return a * b * c

"""
    builder._compile(source_code)
