import hypothesis
import hypothesis.strategies as hst

from opshin.std import fractions as oc_fractions

import math

pos_int = hst.integers(min_value=0)


@hypothesis.given(pos_int, pos_int)
def test_gcd(a: int, b: int):
    assert oc_fractions.gcd(a, b) == math.gcd(a, b), "Invalid gcd"


@hypothesis.given(hst.integers(), hst.integers())
def test_sign(a: int, b: int):
    assert oc_fractions.sign(a) == math.copysign(1, a), "Invalid sign"
