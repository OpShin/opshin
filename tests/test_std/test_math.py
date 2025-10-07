import fractions

import hypothesis
import hypothesis.strategies as hst

from opshin.std import math as oc_math

import math

pos_int = hst.integers(min_value=0)


@hypothesis.given(pos_int, pos_int)
def test_gcd(a: int, b: int):
    assert oc_math.gcd(a, b) == math.gcd(a, b), "Invalid gcd"


@hypothesis.given(hst.integers())
def test_sign(a: int):
    assert oc_math.sign(a) == math.copysign(1, a), "Invalid sign"


@hypothesis.given(hst.binary())
def test_unsigned_int_from_bytes_big(b: bytes):
    assert oc_math.unsigned_int_from_bytes_big(b) == int.from_bytes(
        b, byteorder="big", signed=False
    ), "Invalid from bytes"


@hypothesis.given(hst.integers())
@hypothesis.example(1000)
def test_bytes_big_from_unsigned_int(b: int):
    try:
        res = oc_math.bytes_big_from_unsigned_int(b)
    except AssertionError:
        res = None
    try:
        exp = b.to_bytes(
            max(1, (b.bit_length() + 7) // 8), byteorder="big", signed=False
        )
    except OverflowError:
        exp = None
    assert res == exp, "Invalid to bytes"


@hypothesis.given(hst.integers(), hst.integers())
def test_ceil(a: int, b: int):
    hypothesis.assume(b != 0)
    assert oc_math.ceil(a, b) == math.ceil(fractions.Fraction(a, b)), "Invalid ceil"


@hypothesis.given(hst.integers(), hst.integers())
def test_floor(a: int, b: int):
    hypothesis.assume(b != 0)
    assert oc_math.floor(a, b) == math.floor(fractions.Fraction(a, b)), "Invalid floor"


@hypothesis.given(
    hst.integers(min_value=0, max_value=255), hst.integers(min_value=0, max_value=255)
)
def test_and_8bit(a: int, b: int):
    assert oc_math.and_8bit(a, b) == (a & b), "Invalid and_8bit"


@hypothesis.given(hst.binary(), hst.binary())
@hypothesis.example(b"", b"\x00")
def test_and_bytestring(a: bytes, b: bytes):
    max_len = max(len(a), len(b))
    a_adj = a.rjust(max_len, b"\x00")
    b_adj = b.rjust(max_len, b"\x00")
    expected = bytes(x & y for x, y in zip(a_adj, b_adj))
    assert oc_math.and_bytestring(a, b) == expected, "Invalid and_bytestring"
