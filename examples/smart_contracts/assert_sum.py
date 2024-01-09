#!opshin
from opshin.prelude import *


def validator(datum: int, redeemer: int, context: ScriptContext) -> None:
    purpose = context.purpose
    if not isinstance(purpose, Spending):
        print(f"Wrong script purpose: {purpose}")
    assert (
        datum + redeemer == 42
    ), f"Expected datum and redeemer to sum to 42, but they sum to {datum + redeemer}"
