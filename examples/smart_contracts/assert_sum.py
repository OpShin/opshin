#!opshin
from opshin.prelude import *


def validator(datum: int, redeemer: int, context: ScriptContext) -> None:
    assert (
        datum + redeemer == 42
    ), f"Expected datum and redeemer to sum to 42, but they sum to {datum + redeemer}"
