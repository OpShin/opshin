from eopsin.prelude import *


def validator(n: int) -> List[int]:
    # generate even squares
    return [k * k for k in range(n) if k % 2 == 0]
