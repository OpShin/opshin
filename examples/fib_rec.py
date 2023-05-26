#!opshin


def fib(n: int) -> int:
    if n == 0:
        res = 0
    elif n == 1:
        res = 1
    else:
        res = fib(n - 1) + fib(n - 2)
    return res


def validator(n: int) -> int:
    return fib(n)
