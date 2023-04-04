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
