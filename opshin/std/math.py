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
    acc = 0
    for i in range(len(b)):
        acc = acc * 256 + b[i]
    return acc


def bytes_big_from_unsigned_int(b: int) -> bytes:
    """
    Converts an integer into the corresponding bytestring, big/network byteorder, unsigned

    For example, the integer 66051 will be converted to the bytestring b'\\x01\\x02\\x03'.
    """
    assert b >= 0
    if b == 0:
        return b"\x00"
    acc = b""
    while b > 0:
        acc = bytes([b % 256]) + acc
        b //= 256
    return acc


def ceil(a: int, b: int):
    """Returns a divided by b rounded towards positive infinity"""
    return (a + b - 1) // b if b > 0 else (a + b + 1) // b


def floor(a: int, b: int):
    """Returns a divided by b rounded towards negative infinity"""
    return a // b


EIGHT_BIT_POWERS = [1, 2, 4, 8, 16, 32, 64, 128]


def and_8bit(a: int, b: int) -> int:
    result = 0
    for power in EIGHT_BIT_POWERS:
        bit_a = (a // power) % 2
        bit_b = (b // power) % 2
        bit_and = bit_a * bit_b
        result = result + bit_and * power
    return result


def and_bytestring(a: bytes, b: bytes) -> bytes:
    """Returns the bitwise AND of two bytestrings, padding the shorter one with leading zeros"""
    max_len = max([len(a), len(b)])
    a = a.rjust(max_len, b"\x00")
    b = b.rjust(max_len, b"\x00")
    c = b""
    for i in range(max_len):
        j = max_len - i - 1
        c = cons_byte_string(and_8bit(a[j], b[j]), c)
    return c
