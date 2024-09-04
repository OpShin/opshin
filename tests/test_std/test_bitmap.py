from typing import Tuple

import hypothesis
import hypothesis.strategies as hst

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


@hypothesis.given(bytes_and_index())
def test_test_bitmap(p: Tuple[bytes, int]):
    a, i = p
    ith_bit = int.from_bytes(a, "big") & (1 << ((len(a) * 8) - i - 1))
    assert oc_bitmap.test_bitmap(a, i) == (ith_bit != 0), "Invalid isset check"


@hypothesis.given(bytes_and_index(), hst.booleans())
def test__set_bitmap(p: Tuple[bytes, int], v: bool):
    a, i = p
    if v:
        set_bit = int.from_bytes(a, "big") | (1 << ((len(a) * 8) - i - 1))
    else:
        set_bit = int.from_bytes(a, "big") & (~(1 << ((len(a) * 8) - i - 1)))
    set_bit = set_bit.to_bytes(len(a), byteorder="big")
    assert oc_bitmap._set_bitmap(a, i, v) == set_bit, "Set bit incorrectly"


@hypothesis.given(bytes_and_index())
def test_set_bitmap(p: Tuple[bytes, int]):
    a, i = p
    set_bit = int.from_bytes(a, "big") | (1 << ((len(a) * 8) - i - 1))
    set_bit = set_bit.to_bytes(len(a), byteorder="big")
    assert oc_bitmap.set_bitmap(a, i) == set_bit, "Set bit incorrectly"


@hypothesis.given(bytes_and_index())
def test_reset_bitmap(p: Tuple[bytes, int]):
    a, i = p
    set_bit = int.from_bytes(a, "big") & (~(1 << ((len(a) * 8) - i - 1)))
    set_bit = set_bit.to_bytes(len(a), byteorder="big")
    assert oc_bitmap.reset_bitmap(a, i) == set_bit, "Reset bit incorrectly"


@hypothesis.given(bytes_and_index())
def test_flip_bitmap(p: Tuple[bytes, int]):
    a, i = p
    set_bit = int.from_bytes(a, "big") ^ (1 << ((len(a) * 8) - i - 1))
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
    assert oc_bitmap.test_bitmap(oc_bitmap.set_bitmap(a, i), i), "Set bit incorrectly"


@hypothesis.given(bytes_and_index())
def test_reset_test(p: Tuple[bytes, int]):
    a, i = p
    assert not oc_bitmap.test_bitmap(
        oc_bitmap.reset_bitmap(a, i), i
    ), "Reset bit incorrectly"
