def validator(n: int) -> int:
    return sum([i for i in range(n) if i % 2 == 0])
