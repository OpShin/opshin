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

    def __add__(self, other: Union[Self, int]) -> Self:
        """returns self + other"""
        if isinstance(other, Fraction):
            return Fraction(
                (self.numerator * other.denominator)
                + (other.numerator * self.denominator),
                self.denominator * other.denominator,
            )
        else:
            return Fraction(
                self.numerator + (other * self.denominator), self.denominator
            )

    def __neg__(
        self,
    ) -> Self:
        """returns -self"""
        return Fraction(-self.numerator, self.denominator)

    def __sub__(self, other: Union[Self, int]) -> Self:
        """returns self - other"""
        if isinstance(other, Fraction):
            return Fraction(
                (self.numerator * other.denominator)
                - (other.numerator * self.denominator),
                self.denominator * other.denominator,
            )
        else:
            return Fraction(
                self.numerator - (other * self.denominator), self.denominator
            )

    def __mul__(self, other: Union[Self, int]) -> Self:
        """returns self * other"""
        if isinstance(other, Fraction):
            return Fraction(
                self.numerator * other.numerator, self.denominator * other.denominator
            )
        else:
            return Fraction(self.numerator * other, self.denominator)

    def __truediv__(self, other: Union[Self, int]) -> Self:
        """returns self / other"""
        if isinstance(other, Fraction):
            return Fraction(
                self.numerator * other.denominator, self.denominator * other.numerator
            )
        else:
            return Fraction(self.numerator, self.denominator * other)

    def __ge__(self, other: Union[Self, int]) -> bool:
        """returns self >= other"""
        if isinstance(other, Fraction):
            if self.denominator * other.denominator >= 0:
                res = (
                    self.numerator * other.denominator
                    >= self.denominator * other.numerator
                )
            else:
                res = (
                    self.numerator * other.denominator
                    <= self.denominator * other.numerator
                )
            return res
        else:
            if self.denominator >= 0:
                res = self.numerator >= self.denominator * other
            else:
                res = self.numerator <= self.denominator * other
            return res

    def __le__(self, other: Union[Self, int]) -> bool:
        """returns self <= other"""
        if isinstance(other, Fraction):
            if self.denominator * other.denominator >= 0:
                res = (
                    self.numerator * other.denominator
                    <= self.denominator * other.numerator
                )
            else:
                res = (
                    self.numerator * other.denominator
                    >= self.denominator * other.numerator
                )
            return res
        else:
            if self.denominator >= 0:
                res = self.numerator <= self.denominator * other
            else:
                res = self.numerator >= self.denominator * other
            return res

    def __eq__(self, other: Union[Self, int]) -> bool:
        """returns self == other"""
        if isinstance(other, Fraction):
            return (
                self.numerator * other.denominator == self.denominator * other.numerator
            )
        else:
            return self.numerator == self.denominator * other

    def __lt__(self, other: Union[Self, int]) -> bool:
        """returns self < other"""
        if isinstance(other, Fraction):
            if self.denominator * other.denominator >= 0:
                res = (
                    self.numerator * other.denominator
                    < self.denominator * other.numerator
                )
            else:
                res = (
                    self.numerator * other.denominator
                    > self.denominator * other.numerator
                )
            return res
        else:
            if self.denominator >= 0:
                res = self.numerator < self.denominator * other
            else:
                res = self.numerator > self.denominator * other
            return res

    def __gt__(self, other: Union[Self, int]) -> bool:
        """returns self > other"""
        if isinstance(other, Fraction):
            if self.denominator * other.denominator >= 0:
                res = (
                    self.numerator * other.denominator
                    > self.denominator * other.numerator
                )
            else:
                res = (
                    self.numerator * other.denominator
                    < self.denominator * other.numerator
                )
            return res
        else:
            if self.denominator >= 0:
                res = self.numerator > self.denominator * other
            else:
                res = self.numerator < self.denominator * other
            return res

    def __floordiv__(self, other: Union[Self, int]) -> int:
        if isinstance(other, Fraction):
            x = self / other
            return x.numerator // x.denominator
        else:
            return self.numerator // (other * self.denominator)


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


def ceil_fraction(a: Fraction) -> int:
    return (a.numerator + a.denominator - sign(a.denominator)) // a.denominator
