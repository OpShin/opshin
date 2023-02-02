from eopsin.prelude import *


def validator(datum: int, redeemer: int, context: Nothing) -> None:
    assert datum + redeemer == 42, "Redeemer and datum do not sum to 42"
