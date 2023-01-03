from dataclasses import dataclass


@dataclass(frozen=True)
class PlutusData:
    pass


def main(a: PlutusData, b: PlutusData) -> int:
    return int(a) + int(b)
