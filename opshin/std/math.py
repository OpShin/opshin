""" An implementation of some math operations in opshin """


def gcd(a: int, b: int) -> int:
    while b != 0:
        a, b = b, a % b
    return abs(a)


def sign(a: int) -> int:
    return -1 if a < 0 else 1


def unsigned_int_from_bytes_big(b: bytes) -> int:
    """Converts a bytestring into the corresponding integer, big/network byteorder, unsigned"""
    acc = 0
    for i in range(len(b)):
        acc = acc * 256 + b[i]
    return acc


def bytes_big_from_unsigned_int(b: int) -> bytes:
    """Converts an integer into the corresponding bytestring, big/network byteorder, unsigned"""
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
