import hypothesis
import hypothesis.strategies as hst

from opshin.std import fractions as oc_fractions

import fractions as native_fractions
import math as native_math

non_null = hst.one_of(hst.integers(min_value=1), hst.integers(max_value=-1))
denormalized_fractions = hst.builds(oc_fractions.Fraction, hst.integers(), non_null)
denormalized_fractions_non_null = hst.builds(oc_fractions.Fraction, non_null, non_null)


def native_fraction_from_oc_fraction(f: oc_fractions.Fraction):
    return native_fractions.Fraction(f.numerator, f.denominator)


@hypothesis.given(denormalized_fractions, denormalized_fractions)
def test_add(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_added = oc_fractions.add_fraction(a, b)
    oc_normalized = native_fraction_from_oc_fraction(oc_added)
    assert oc_normalized == (
        native_fraction_from_oc_fraction(a) + native_fraction_from_oc_fraction(b)
    ), "Invalid add"


@hypothesis.given(denormalized_fractions, denormalized_fractions)
def test_sub(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_subbed = oc_fractions.sub_fraction(a, b)
    oc_normalized = native_fraction_from_oc_fraction(oc_subbed)
    assert oc_normalized == (
        native_fraction_from_oc_fraction(a) - native_fraction_from_oc_fraction(b)
    ), "Invalid sub"


@hypothesis.given(denormalized_fractions)
def test_neg(a: oc_fractions.Fraction):
    oc_negged = oc_fractions.neg_fraction(a)
    oc_normalized = native_fraction_from_oc_fraction(oc_negged)
    assert oc_normalized == -native_fraction_from_oc_fraction(a), "Invalid neg"


@hypothesis.given(denormalized_fractions, denormalized_fractions)
def test_mul(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_mulled = oc_fractions.mul_fraction(a, b)
    oc_normalized = native_fraction_from_oc_fraction(oc_mulled)
    assert oc_normalized == (
        native_fraction_from_oc_fraction(a) * native_fraction_from_oc_fraction(b)
    ), "Invalid mul"


@hypothesis.given(denormalized_fractions, denormalized_fractions_non_null)
def test_div(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_divved = oc_fractions.div_fraction(a, b)
    oc_normalized = native_fraction_from_oc_fraction(oc_divved)
    assert oc_normalized == (
        native_fraction_from_oc_fraction(a) / native_fraction_from_oc_fraction(b)
    ), "Invalid div"


@hypothesis.given(denormalized_fractions)
def test_norm_sign(a: oc_fractions.Fraction):
    oc_normed = oc_fractions._norm_signs_fraction(a)
    assert oc_normed.denominator > 0, "invalid norm_signs"
    oc_normalized = native_fraction_from_oc_fraction(oc_normed)
    oc_a_normalized = native_fraction_from_oc_fraction(a)
    assert oc_normalized == oc_a_normalized, "invalid norm_signs"


@hypothesis.given(denormalized_fractions)
@hypothesis.example(oc_fractions.Fraction(0, -1))
def test_norm(a: oc_fractions.Fraction):
    oc_normed = oc_fractions.norm_fraction(a)
    oc_normalized = native_fraction_from_oc_fraction(a)
    assert oc_normed.numerator == oc_normalized.numerator, "Invalid norm"
    assert oc_normed.denominator == oc_normalized.denominator, "Invalid norm"


@hypothesis.given(denormalized_fractions, denormalized_fractions)
def test_ge(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_ge = oc_fractions.ge_fraction(a, b)
    ge = native_fraction_from_oc_fraction(a) >= native_fraction_from_oc_fraction(b)
    assert oc_ge == ge, "Invalid ge"


@hypothesis.given(denormalized_fractions, denormalized_fractions)
def test_le(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_le = oc_fractions.le_fraction(a, b)
    le = native_fraction_from_oc_fraction(a) <= native_fraction_from_oc_fraction(b)
    assert oc_le == le, "Invalid le"


@hypothesis.given(denormalized_fractions, denormalized_fractions)
def test_lt(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_lt = oc_fractions.lt_fraction(a, b)
    lt = native_fraction_from_oc_fraction(a) < native_fraction_from_oc_fraction(b)
    assert oc_lt == lt, "Invalid lt"


@hypothesis.given(denormalized_fractions, denormalized_fractions)
def test_gt(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_gt = oc_fractions.gt_fraction(a, b)
    gt = native_fraction_from_oc_fraction(a) > native_fraction_from_oc_fraction(b)
    assert oc_gt == gt, "Invalid gt"


@hypothesis.given(denormalized_fractions, denormalized_fractions)
def test_eq(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_eq = oc_fractions.eq_fraction(a, b)
    eq = native_fraction_from_oc_fraction(a) == native_fraction_from_oc_fraction(b)
    assert oc_eq == eq, "Invalid eq"


@hypothesis.given(denormalized_fractions)
def test_floor(a: oc_fractions.Fraction):
    oc_floor = oc_fractions.floor_fraction(a)
    assert (
        native_math.floor(native_fraction_from_oc_fraction(a)) == oc_floor
    ), "Invalid floor"


@hypothesis.given(denormalized_fractions)
def test_ceil(a: oc_fractions.Fraction):
    oc_ceil = oc_fractions.ceil_fraction(a)
    assert (
        native_math.ceil(native_fraction_from_oc_fraction(a)) == oc_ceil
    ), "Invalid ceil"
