#!opshin
from opshin.prelude import *


def validator(n: int, even: bool) -> Dict[int, int]:
    if even:
        # generate even squares
        res = {k: k * k for k in range(n) if k % 2 == 0}
    else:
        # generate all squares
        res = {k: k * k for k in range(n)}
    return res
