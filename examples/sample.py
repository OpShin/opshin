from eopsin.prelude import *


def main(n: int, m: int) -> bool:
    fine = False
    if int(n) + int(m) == 42:
        fine = True
    return fine
