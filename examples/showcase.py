from eopsin.prelude import *


def validator(n: int) -> int:
    a, b = 3, n
    if b < 5:
        print("add")
        a += 5
    x = sha256(b"123").digest()
    assert x[1:3] == b"e\xa4", "Hash is wrong"
    y = [1, 2]
    return a + len(x) + len(y)
