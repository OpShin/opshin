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
def test_isset_bitmap(p: Tuple[bytes, int]):
    a, i = p
    ith_bit = int.from_bytes(a, "big") & (1 << ((len(a) * 8) - i - 1))
    assert oc_bitmap.isset_bitmap(a, i) == (ith_bit != 0), "Invalid isset check"


@hypothesis.given(bytes_and_index(), hst.booleans())
def test_set_bitmap(p: Tuple[bytes, int], v: bool):
    a, i = p
    if v:
        set_bit = int.from_bytes(a, "big") | (1 << ((len(a) * 8) - i - 1))
    else:
        set_bit = int.from_bytes(a, "big") & (~(1 << ((len(a) * 8) - i - 1)))
    set_bit = set_bit.to_bytes(len(a), byteorder="big")
    assert oc_bitmap.set_bitmap(a, i, v) == set_bit, "Set bit incorrectly"
