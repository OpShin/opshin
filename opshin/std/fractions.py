"""
An implementation of fractions in opshin
This does not maintain smallest possible notation invariants for the sake of efficiency
- the user has full control over when to normalize the fractions and should do so using norm_fraction
"""

from dataclasses import dataclass
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union
from typing import Self

from opshin.std.math import *


@dataclass(unsafe_hash=True)
class Fraction(PlutusData):
    CONSTR_ID = 1
    numerator: int
    denominator: int

    def norm(self) -> Self:
        """Restores the invariant that num/denom are in the smallest possible denomination and denominator > 0"""
        return _norm_gcd_fraction(_norm_signs_fraction(self))

    def ceil(self) -> int:
        return (
            self.numerator + self.denominator - sign(self.denominator)
        ) // self.denominator

    def __add__(self, other: Self) -> Self:
        """returns self + other"""
        return Fraction(
            (self.numerator * other.denominator) + (other.numerator * self.denominator),
            self.denominator * other.denominator,
        )

    def __neg__(
        self,
    ) -> Self:
        """returns -self"""
        return Fraction(-self.numerator, self.denominator)

    def __sub__(self, other: Self) -> Self:
        """returns self - other"""
        return Fraction(
            (self.numerator * other.denominator) - (other.numerator * self.denominator),
            self.denominator * other.denominator,
        )

    def __mul__(self, other: Self) -> Self:
        """returns self * other"""
        return Fraction(
            self.numerator * other.numerator, self.denominator * other.denominator
        )

    def __truediv__(self, other: Self) -> Self:
        """returns self / other"""
        return Fraction(
            self.numerator * other.denominator, self.denominator * other.numerator
        )

    def __ge__(self, other: Self) -> Self:
        """returns self >= other"""
        if self.denominator * other.denominator >= 0:
            res = (
                self.numerator * other.denominator >= self.denominator * other.numerator
            )
        else:
            res = (
                self.numerator * other.denominator <= self.denominator * other.numerator
            )
        return res

    def __le__(self, other: Self) -> Self:
        """returns self <= other"""
        if self.denominator * other.denominator >= 0:
            res = (
                self.numerator * other.denominator <= self.denominator * other.numerator
            )
        else:
            res = (
                self.numerator * other.denominator >= self.denominator * other.numerator
            )
        return res

    def __eq__(self, other: Self) -> Self:
        """returns self == other"""
        return self.numerator * other.denominator == self.denominator * other.numerator

    def __lt__(self, other: Self) -> Self:
        """returns self < other"""
        if self.denominator * other.denominator >= 0:
            res = (
                self.numerator * other.denominator < self.denominator * other.numerator
            )
        else:
            res = (
                self.numerator * other.denominator > self.denominator * other.numerator
            )
        return res

    def __gt__(self, other: Self) -> Self:
        """returns self > other"""
        if self.denominator * other.denominator >= 0:
            res = (
                self.numerator * other.denominator > self.denominator * other.numerator
            )
        else:
            res = (
                self.numerator * other.denominator < self.denominator * other.numerator
            )
        return res

    def __floordiv__(self, other: Self) -> int:
        x = self / other
        return x.numerator // x.denominator


def add_fraction(a: Fraction, b: Fraction) -> Fraction:
    """returns self + other"""
    return Fraction(
        (a.numerator * b.denominator) + (b.numerator * a.denominator),
        a.denominator * b.denominator,
    )


def neg_fraction(a: Fraction) -> Fraction:
    """returns -a"""
    return Fraction(-a.numerator, a.denominator)


def sub_fraction(a: Fraction, b: Fraction) -> Fraction:
    """returns self - other"""
    return add_fraction(a, neg_fraction(b))


def mul_fraction(a: Fraction, b: Fraction) -> Fraction:
    """returns self * other"""
    return Fraction(a.numerator * b.numerator, a.denominator * b.denominator)


def div_fraction(a: Fraction, b: Fraction) -> Fraction:
    """returns self / other"""
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
    """returns self >= other"""
    if a.denominator * b.denominator >= 0:
        res = a.numerator * b.denominator >= a.denominator * b.numerator
    else:
        res = a.numerator * b.denominator <= a.denominator * b.numerator
    return res


def le_fraction(a: Fraction, b: Fraction) -> bool:
    """returns self <= other"""
    if a.denominator * b.denominator >= 0:
        res = a.numerator * b.denominator <= a.denominator * b.numerator
    else:
        res = a.numerator * b.denominator >= a.denominator * b.numerator
    return res


def eq_fraction(a: Fraction, b: Fraction) -> bool:
    """returns self == other"""
    return a.numerator * b.denominator == a.denominator * b.numerator


def lt_fraction(a: Fraction, b: Fraction) -> bool:
    """returns self < other"""
    if a.denominator * b.denominator >= 0:
        res = a.numerator * b.denominator < a.denominator * b.numerator
    else:
        res = a.numerator * b.denominator > a.denominator * b.numerator
    return res


def gt_fraction(a: Fraction, b: Fraction) -> bool:
    """returns self > other"""
    if a.denominator * b.denominator >= 0:
        res = a.numerator * b.denominator > a.denominator * b.numerator
    else:
        res = a.numerator * b.denominator < a.denominator * b.numerator
    return res


def floor_fraction(a: Fraction) -> int:
    return a.numerator // a.denominator


def ceil_fraction(a: Fraction) -> int:
    return (a.numerator + a.denominator - sign(a.denominator)) // a.denominator
