from eopsin.prelude import *


def validator(n: int, even: bool) -> List[int]:
    if even:
        # generate even squares
        res = [k * k for k in range(n) if k % 2 == 0]
    else:
        # generate all squares
        res = [k * k for k in range(n)]
    return res
