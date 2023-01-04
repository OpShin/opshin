from eopsin.prelude import *


def main(n: int) -> None:
    a, b = 0, int(n)
    if b < 5:
        print("add")
        a += 5
    else:
        print("sub")
        a -= b
    return a
