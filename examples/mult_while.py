#!opshin


def validator(a: int, b: int) -> int:
    # trivial implementation of c = a * b
    c = 0
    while 0 < b:
        c += a
        b -= 1
    return c
