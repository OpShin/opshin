""" An implementation of some math operations in eopsin """


def gcd(a: int, b: int):
    while b != 0:
        a, b = b, a % b
    return abs(a)


def sign(a: int):
    return -1 if a < 0 else 1
