def validator(a: int, b: int) -> int:
    # trivial implementation of c = a * b
    c = 0
    for k in range(b):
        c += a
    return c
