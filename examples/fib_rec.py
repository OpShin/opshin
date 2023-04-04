from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


def fib(n: int) -> int:
    Requires(n >= 0)
    Requires(MustTerminate(n + 1))
    if n == 0:
        res = 0
    elif n == 1:
        res = 1
    else:
        res = fib(n - 1) + fib(n - 2)
    return res


def validator(n: int) -> int:
    Requires(n >= 0)
    return fib(n)
