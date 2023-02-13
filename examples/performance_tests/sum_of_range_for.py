def validator(n: int) -> int:
    s = 0
    for i in range(n):
        if i % 2 == 0:
            s += i
    return s
