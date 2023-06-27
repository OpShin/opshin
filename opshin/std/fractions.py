"""
An implementation of fractions in opshin
This does not maintain smallest possible notation invariants for the sake of efficiency
- the user has full control over when to normalize the fractions and should do so using norm_fraction
"""
from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union

from opshin.std.math import *


@dataclass(unsafe_hash=True)
class Fraction(PlutusData):
    CONSTR_ID = 1
    numerator: int
    denominator: int


def add_fraction(a: Fraction, b: Fraction) -> Fraction:
    """returns a + b"""
    return Fraction(
        (a.numerator * b.denominator) + (b.numerator * a.denominator),
        a.denominator * b.denominator,
    )


def neg_fraction(a: Fraction) -> Fraction:
    """returns -a"""
    return Fraction(-a.numerator, a.denominator)


def sub_fraction(a: Fraction, b: Fraction) -> Fraction:
    """returns a - b"""
    return add_fraction(a, neg_fraction(b))


def mul_fraction(a: Fraction, b: Fraction) -> Fraction:
    """returns a * b"""
    return Fraction(a.numerator * b.numerator, a.denominator * b.denominator)


def div_fraction(a: Fraction, b: Fraction) -> Fraction:
    """returns a / b"""
    return Fraction(a.numerator * b.denominator, a.denominator * b.numerator)


def _norm_signs_fraction(a: Fraction) -> Fraction:
    """Restores the invariant that the denominator is > 0"""
    return Fraction(sign(a.denominator) * a.numerator, abs(a.denominator))


def _norm_gcd_fraction(a: Fraction) -> Fraction:
    """Restores the invariant that num/denom are in the smallest possible denomination"""
    g = gcd(a.numerator, a.denominator)
    return Fraction(a.numerator // g, a.denominator // g)


def norm_fraction(a: Fraction) -> Fraction:
    """Restores the invariant that num/denom are in the smallest possible denomination and denominator > 0"""
    return _norm_gcd_fraction(_norm_signs_fraction(a))


def ge_fraction(a: Fraction, b: Fraction) -> bool:
    """returns a >= b"""
    if a.denominator * b.denominator >= 0:
        res = a.numerator * b.denominator >= a.denominator * b.numerator
    else:
        res = a.numerator * b.denominator <= a.denominator * b.numerator
    return res


def le_fraction(a: Fraction, b: Fraction) -> bool:
    """returns a <= b"""
    if a.denominator * b.denominator >= 0:
        res = a.numerator * b.denominator <= a.denominator * b.numerator
    else:
        res = a.numerator * b.denominator >= a.denominator * b.numerator
    return res


def eq_fraction(a: Fraction, b: Fraction) -> bool:
    """returns a == b"""
    return a.numerator * b.denominator == a.denominator * b.numerator


def lt_fraction(a: Fraction, b: Fraction) -> bool:
    """returns a < b"""
    if a.denominator * b.denominator >= 0:
        res = a.numerator * b.denominator < a.denominator * b.numerator
    else:
        res = a.numerator * b.denominator > a.denominator * b.numerator
    return res


def gt_fraction(a: Fraction, b: Fraction) -> bool:
    """returns a > b"""
    if a.denominator * b.denominator >= 0:
        res = a.numerator * b.denominator > a.denominator * b.numerator
    else:
        res = a.numerator * b.denominator < a.denominator * b.numerator
    return res


def floor_fraction(a: Fraction) -> int:
    return a.numerator // a.denominator


def ceil_fraction(a: Fraction) -> int:
    return (a.numerator + a.denominator - sign(a.denominator)) // a.denominator
