from dataclasses import dataclass


@dataclass(frozen=True)
class PlutusData:
    pass


def main(n: PlutusData) -> None:
    a, b = 0, int(n)
    if b < 5:
        print("add")
        a += 5
    else:
        print("sub")
        a -= b
    return a
