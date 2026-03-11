#!opshin
from opshin.prelude import *


def validator(n: int, even: bool) -> List[int]:
    pairs = [[k, k] for k in range(n)]
    if even:
        # generate even squares
        res = [a * b for a, b in pairs if a % 2 == 0]
    else:
        # generate all squares
        res = [a * b for a, b in pairs]
    return res
