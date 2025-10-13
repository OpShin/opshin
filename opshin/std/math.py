"""An implementation of some math operations in opshin"""

from opshin.std.builtins import *


def gcd(a: int, b: int) -> int:
    """Returns the greatest common divisor of a and b"""
    while b != 0:
        a, b = b, a % b
    return abs(a)


def sign(a: int) -> int:
    """Returns the sign of a: -1 if a < 0, 0 if a == 0, 1 if a > 0"""
    return -1 if a < 0 else 1


def unsigned_int_from_bytes_big(b: bytes) -> int:
    """
    Converts a bytestring into the corresponding integer, big/network byteorder, unsigned

    For example, the bytestring b'\\x01\\x02\\x03' will be converted to the integer 66051.
    """
    return byte_string_to_integer(True, b)


def bytes_big_from_unsigned_int(b: int) -> bytes:
    """
    Converts an integer into the corresponding bytestring of minimal width, big/network byteorder, unsigned

    For example, the integer 66051 will be converted to the bytestring b'\\x01\\x02\\x03'.
    """
    return integer_to_byte_string(True, b, 0)


def ceil(a: int, b: int):
    """Returns a divided by b rounded towards positive infinity"""
    return (a + b - 1) // b if b > 0 else (a + b + 1) // b


def floor(a: int, b: int):
    """Returns a divided by b rounded towards negative infinity"""
    return a // b


def and_bytestring(a: bytes, b: bytes) -> bytes:
    """Returns the bitwise AND of two bytestrings, padding the shorter one with leading ones"""
    return and_byte_string(True, a, b)
