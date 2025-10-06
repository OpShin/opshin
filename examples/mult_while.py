#!opshin


def validator(a: int, b: int) -> int:
    # trivial implementation of c = a * b
    c = 0
    while b > 0:
        c += a
        b -= 1
    return c
