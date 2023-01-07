def validator(n: int) -> int:
    a = 3
    b = n
    if b < 5:
        print("add")
        a += 5
    else:
        print("sub")
        a -= b
    return a
