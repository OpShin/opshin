#!opshin
from opshin.prelude import *


def validator(n: int, even: bool) -> Dict[int, int]:
    pairs = {k: k for k in range(n)}
    if even:
        # generate even squares
        res = {k: v * k for k, v in pairs.items() if k % 2 == 0}
    else:
        # generate all squares
        res = {k: v * k for k, v in pairs.items()}
    return res
