"""
An implementation of fractions in opshin

Fractions internally are represented as a pair of integers (numerator, denominator).
The representation in OpShin does not maintain smallest possible notation invariants for the sake of efficiency
- the user has full control over when to normalize the fractions and should do so using norm_fraction

Fractions support all arithmetic operations, comparisons, and some additional methods like ceil, you can even use them with integers.
For example, you can do:
```
from opshin.std.fractions import *
a = Fraction(1, 2)
b = Fraction(3, 4)
c = a + b  # c is Fraction(5, 4)
d = a * 2  # d is Fraction(2, 2)
d.norm()  # d is Fraction(1, 1)
e = a.ceil()  # e is Fraction(1, 1)
f = a > b  # f is False
```

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

    def norm(self) -> "Fraction":
        """Restores the invariant that num/denom are in the smallest possible denomination and denominator > 0"""
        return _norm_gcd_fraction(_norm_signs_fraction(self))

    def ceil(self) -> int:
        return (
            self.numerator + self.denominator - sign(self.denominator)
        ) // self.denominator

    def floor(self) -> int:
        return (self.numerator) // self.denominator

    def __add__(self, other: Union["Fraction", int]) -> "Fraction":
        """returns self + other"""
        if isinstance(other, Fraction):
            return Fraction(
                (self.numerator * other.denominator)
                + (other.numerator * self.denominator),
                self.denominator * other.denominator,
            )
        else:
            return Fraction(
                (self.numerator) + (other * self.denominator),
                self.denominator,
            )

    def __neg__(
        self,
    ) -> "Fraction":
        """returns -self"""
        return Fraction(-self.numerator, self.denominator)

    def __sub__(self, other: Union["Fraction", int]) -> "Fraction":
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

    def __mul__(self, other: Union["Fraction", int]) -> "Fraction":
        """returns self * other"""
        if isinstance(other, Fraction):
            return Fraction(
                self.numerator * other.numerator, self.denominator * other.denominator
            )
        else:
            return Fraction(self.numerator * other, self.denominator)

    def __truediv__(self, other: Union["Fraction", int]) -> "Fraction":
        """returns self / other"""
        if isinstance(other, Fraction):
            return Fraction(
                self.numerator * other.denominator, self.denominator * other.numerator
            )
        else:
            return Fraction(self.numerator, self.denominator * other)

    def __pow__(self, exponent: int) -> "Fraction":
        """returns self ** exponent, where exponent is an integer"""
        if exponent >= 0:
            return Fraction(self.numerator**exponent, self.denominator**exponent)
        else:
            return Fraction(
                self.denominator ** (-exponent), self.numerator ** (-exponent)
            )

    def __ge__(self, other: Union["Fraction", int]) -> bool:
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

    def __le__(self, other: Union["Fraction", int]) -> bool:
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

    def __eq__(self, other: Union["Fraction", int]) -> bool:
        """returns self == other"""
        if isinstance(other, Fraction):
            return (
                self.numerator * other.denominator == self.denominator * other.numerator
            )
        else:
            return self.numerator == self.denominator * other

    def __lt__(self, other: Union["Fraction", int]) -> bool:
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

    def __gt__(self, other: Union["Fraction", int]) -> bool:
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

    def __floordiv__(self, other: Union["Fraction", int]) -> int:
        if isinstance(other, Fraction):
            x = self / other
            return x.numerator // x.denominator
        else:
            return self.numerator // (other * self.denominator)

    def __radd__(self, other: Union["Fraction", int]) -> "Fraction":
        return self + other

    def __rsub__(self, other: Union["Fraction", int]) -> "Fraction":
        return -self + other

    def __rmul__(self, other: Union["Fraction", int]) -> "Fraction":
        return self * other

    def __rtruediv__(self, other: Union["Fraction", int]) -> "Fraction":
        if isinstance(other, Fraction):
            return other / self
        else:
            return Fraction(other * self.denominator, self.numerator)

    def __rfloordiv__(self, other: Union["Fraction", int]) -> int:
        if isinstance(other, Fraction):
            return other // self
        else:
            x = Fraction(other, 1) / self
            return x.numerator // x.denominator


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


def floor_fraction(a: Fraction) -> int:
    return a.numerator // a.denominator
