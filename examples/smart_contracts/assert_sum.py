#!opshin
from opshin.prelude import *


def validator(context: ScriptContext) -> None:
    datum = own_datum(context)
    redeemer = context.redeemer
    assert (
        datum + redeemer == 42
    ), f"Expected datum and redeemer to sum to 42, but they sum to {datum + redeemer}"
