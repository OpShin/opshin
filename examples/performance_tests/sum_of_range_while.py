def validator(n: int) -> int:
    s = 0
    i = 0
    while i < n:
        if i % 2 == 0:
            s += i
        i += 1
    return s
