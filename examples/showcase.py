def validator(n: int) -> int:
    a, b = 3, n
    if b < 5:
        print("add")
        a += 5
    else:
        print("sub")
        a -= b
    return a
