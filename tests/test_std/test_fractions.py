import hypothesis
import hypothesis.strategies as hst
from typing import Union

from hypothesis.strategies import integers

from opshin.std import fractions as oc_fractions
from ..utils import eval_uplc, eval_uplc_value

import fractions as native_fractions
import math as native_math

from uplc.ast import PlutusConstr

non_null = hst.one_of(hst.integers(min_value=1), hst.integers(max_value=-1))
denormalized_fractions = hst.builds(oc_fractions.Fraction, hst.integers(), non_null)
denormalized_fractions_non_null = hst.builds(oc_fractions.Fraction, non_null, non_null)
denormalized_fractions_and_int = hst.one_of([denormalized_fractions, hst.integers()])
denormalized_fractions_and_int_non_null = hst.one_of(
    [denormalized_fractions_non_null, non_null]
)


def native_fraction_from_oc_fraction(f: Union[oc_fractions.Fraction, int]):
    if isinstance(f, oc_fractions.Fraction):
        return native_fractions.Fraction(f.numerator, f.denominator)
    elif isinstance(f, PlutusConstr):
        return native_fractions.Fraction(*[x.value for x in f.fields])
    else:
        return f


def plutus_to_native(f):
    assert isinstance(f, PlutusConstr)
    assert f.constructor == 1
    return native_fractions.Fraction(*[field.value for field in f.fields])


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int)
def test_add_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_added = a + b
    oc_normalized = native_fraction_from_oc_fraction(oc_added)
    assert oc_normalized == (
        native_fraction_from_oc_fraction(a) + native_fraction_from_oc_fraction(b)
    ), "Invalid add"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int)
def test_sub_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_subbed = a - b
    oc_normalized = native_fraction_from_oc_fraction(oc_subbed)
    assert oc_normalized == (
        native_fraction_from_oc_fraction(a) - native_fraction_from_oc_fraction(b)
    ), "Invalid sub"


@hypothesis.given(denormalized_fractions)
def test_neg_dunder(a: oc_fractions.Fraction):
    oc_negged = -a
    oc_normalized = native_fraction_from_oc_fraction(oc_negged)
    assert oc_normalized == -native_fraction_from_oc_fraction(a), "Invalid neg"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int)
def test_mul_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_mulled = a * b
    oc_normalized = native_fraction_from_oc_fraction(oc_mulled)
    assert oc_normalized == (
        native_fraction_from_oc_fraction(a) * native_fraction_from_oc_fraction(b)
    ), "Invalid mul"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int_non_null)
def test_div_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_divved = a / b
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


@hypothesis.given(denormalized_fractions)
@hypothesis.example(oc_fractions.Fraction(0, -1))
def test_norm_method(a: oc_fractions.Fraction):
    oc_normed = a.norm()
    oc_normalized = native_fraction_from_oc_fraction(a)
    assert oc_normed.numerator == oc_normalized.numerator, "Invalid norm"
    assert oc_normed.denominator == oc_normalized.denominator, "Invalid norm"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int)
def test_ge_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_ge = a >= b
    ge = native_fraction_from_oc_fraction(a) >= native_fraction_from_oc_fraction(b)
    assert oc_ge == ge, "Invalid ge"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int)
def test_le_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_le = a <= b
    le = native_fraction_from_oc_fraction(a) <= native_fraction_from_oc_fraction(b)
    assert oc_le == le, "Invalid le"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int)
def test_lt(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_lt = a < b
    lt = native_fraction_from_oc_fraction(a) < native_fraction_from_oc_fraction(b)
    assert oc_lt == lt, "Invalid lt"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int)
def test_gt_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_gt = a > b
    gt = native_fraction_from_oc_fraction(a) > native_fraction_from_oc_fraction(b)
    assert oc_gt == gt, "Invalid gt"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int)
def test_eq_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_eq = a == b
    eq = native_fraction_from_oc_fraction(a) == native_fraction_from_oc_fraction(b)
    assert oc_eq == eq, "Invalid eq"


@hypothesis.given(denormalized_fractions, denormalized_fractions_and_int_non_null)
def test_floor_dunder(a: oc_fractions.Fraction, b: oc_fractions.Fraction):
    oc_floor = a // b
    floor = native_fraction_from_oc_fraction(a) // native_fraction_from_oc_fraction(b)

    assert oc_floor == floor, "Invalid floor"


@hypothesis.given(denormalized_fractions, hst.integers(max_value=10, min_value=-10))
def test_pow_dunder(a: oc_fractions.Fraction, b: int):
    if a == 0:
        return
    oc_le = a**b
    le = native_fraction_from_oc_fraction(a) ** b
    assert oc_le == le, "Invalid pow"


@hypothesis.given(denormalized_fractions)
def test_ceil(a: oc_fractions.Fraction):
    oc_ceil = oc_fractions.ceil_fraction(a)
    assert (
        native_math.ceil(native_fraction_from_oc_fraction(a)) == oc_ceil
    ), "Invalid ceil"


@hypothesis.given(denormalized_fractions)
def test_floor(a: oc_fractions.Fraction):
    oc_ceil = oc_fractions.floor_fraction(a)
    assert (
        native_math.floor(native_fraction_from_oc_fraction(a)) == oc_ceil
    ), "Invalid ceil"


@hypothesis.given(denormalized_fractions)
def test_ceil_method(a: oc_fractions.Fraction):
    oc_ceil = a.ceil()
    assert (
        native_math.ceil(native_fraction_from_oc_fraction(a)) == oc_ceil
    ), "Invalid ceil"


@hypothesis.given(denormalized_fractions)
def test_floor_method(a: oc_fractions.Fraction):
    oc_ceil = a.floor()
    assert (
        native_math.floor(native_fraction_from_oc_fraction(a)) == oc_ceil
    ), "Invalid ceil"


@hypothesis.given(
    denormalized_fractions, hst.one_of(denormalized_fractions, hst.integers())
)
def test_uplc_add_frac_union(a, b):
    source_code = """
from opshin.std.fractions import *
from typing import Dict, List, Union

def validator(a: Fraction, b: Union[Fraction, int]) -> Fraction:
    return a+b
"""
    ret = eval_uplc(source_code, a, b)
    assert (
        native_fraction_from_oc_fraction(a) + native_fraction_from_oc_fraction(b)
    ) == native_fraction_from_oc_fraction(ret), "invalid add"


@hypothesis.given(denormalized_fractions, hst.integers())
def test_uplc_add_frac_int(a, b):
    source_code = """
from opshin.std.fractions import *
from typing import Dict, List, Union

def validator(a: Fraction, b: int) -> Fraction:
    return a+b
"""
    ret = eval_uplc(source_code, a, b)
    assert (
        native_fraction_from_oc_fraction(a) + b
    ) == native_fraction_from_oc_fraction(ret), "invalid add"


@hypothesis.given(hst.integers(), denormalized_fractions)
def test_uplc_add_int_frac(a, b):
    source_code = """
from opshin.std.fractions import *
from typing import Dict, List, Union

def validator(a: int, b: Fraction) -> Fraction:
    return a+b
"""
    ret = eval_uplc(source_code, a, b)
    assert (
        native_fraction_from_oc_fraction(a) + b
    ) == native_fraction_from_oc_fraction(ret), "invalid add"


@hypothesis.given(hst.integers(), denormalized_fractions)
@hypothesis.example(0, oc_fractions.Fraction(1, 2))
def test_uplc_mul_int_frac(a, b):
    source_code = """
from opshin.std.fractions import *
from typing import Dict, List, Union

def validator(a: int, b: Fraction) -> Fraction:
    return a*b
"""
    ret = eval_uplc(source_code, a, b)
    assert (
        native_fraction_from_oc_fraction(a) * b
    ) == native_fraction_from_oc_fraction(ret), "invalid mul"


@hypothesis.given(denormalized_fractions, hst.integers())
@hypothesis.example(oc_fractions.Fraction(1, 2), 0)
def test_uplc_mul_frac_int(a, b):
    source_code = """
from opshin.std.fractions import *
from typing import Dict, List, Union

def validator(a: Fraction, b: int) -> Fraction:
    return a*b
"""
    ret = eval_uplc(source_code, a, b)
    assert (
        native_fraction_from_oc_fraction(a) * b
    ) == native_fraction_from_oc_fraction(ret), "invalid mul"


@hypothesis.given(
    denormalized_fractions, hst.one_of(denormalized_fractions, hst.integers())
)
def test_uplc_mul_frac_union(a, b):
    source_code = """
from opshin.std.fractions import *
from typing import Dict, List, Union

def validator(a: Fraction, b: Union[Fraction, int]) -> Fraction:
    return a*b
"""
    ret = eval_uplc(source_code, a, b)
    assert (
        native_fraction_from_oc_fraction(a) * native_fraction_from_oc_fraction(b)
    ) == native_fraction_from_oc_fraction(ret), "invalid mul"


@hypothesis.given(denormalized_fractions, hst.integers())
@hypothesis.example(oc_fractions.Fraction(1, 2), 0)
def test_uplc_mul_fractions_unnamed(a: oc_fractions.Fraction, b):
    source_code = """
from opshin.std.fractions import *
from typing import Dict, List, Union

def validator(a: int, b:int, c: int) -> Fraction:
    return Fraction(a,b) * c

"""
    ret = eval_uplc(source_code, a.numerator, a.denominator, b)
    assert (
        native_fraction_from_oc_fraction(a) * native_fraction_from_oc_fraction(b)
    ) == native_fraction_from_oc_fraction(ret), "invalid mul"


@hypothesis.given(hst.integers(), denormalized_fractions)
def test_radd_dunder(a: int, b: oc_fractions.Fraction):
    oc_added = a + b
    oc_normalized = native_fraction_from_oc_fraction(oc_added)
    assert oc_normalized == (a + native_fraction_from_oc_fraction(b)), "Invalid radd"


@hypothesis.given(hst.integers(), denormalized_fractions)
def test_rsub_dunder(a: int, b: oc_fractions.Fraction):
    oc_subbed = a - b
    oc_normalized = native_fraction_from_oc_fraction(oc_subbed)
    assert oc_normalized == (a - native_fraction_from_oc_fraction(b)), "Invalid rsub"


@hypothesis.given(hst.integers(), denormalized_fractions)
def test_rmul_dunder(a: int, b: oc_fractions.Fraction):
    oc_mulled = a * b
    oc_normalized = native_fraction_from_oc_fraction(oc_mulled)
    assert oc_normalized == (a * native_fraction_from_oc_fraction(b)), "Invalid rmul"


@hypothesis.given(hst.integers(), denormalized_fractions_non_null)
def test_rtruediv_dunder(a: int, b: oc_fractions.Fraction):
    oc_divved = a / b
    oc_normalized = native_fraction_from_oc_fraction(oc_divved)
    assert oc_normalized == (
        a / native_fraction_from_oc_fraction(b)
    ), "Invalid rtruediv"


@hypothesis.given(hst.integers(), denormalized_fractions_non_null)
def test_rfloordiv_dunder(a: int, b: oc_fractions.Fraction):
    oc_floordivved = a // b
    floordivved = a // native_fraction_from_oc_fraction(b)
    assert oc_floordivved == floordivved, "Invalid rfloordiv"
