import hypothesis
import hypothesis.strategies as hst

from opshin.std import bitmap as oc_bitmap


@hypothesis.given(hst.integers())
def test_init_bitmap(x: int):
    assert oc_bitmap.init_bitmap(x) == [False for _ in range(x)], "Invalid gcd"


@hypothesis.given(hst.integers())
def test_sign(a: int):
    assert oc_math.sign(a) == math.copysign(1, a), "Invalid sign"


@hypothesis.given(hst.binary())
def test_unsigned_int_from_bytes_big(b: bytes):
    assert oc_math.unsigned_int_from_bytes_big(b) == int.from_bytes(
        b, byteorder="big", signed=False
    ), "Invalid from bytes"
