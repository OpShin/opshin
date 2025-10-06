#!opshin
from opshin.prelude import *


# this validator will print the datum, redeemer and script context passed from the node in a readable format
def validator(d, r, context: ScriptContext):
    print(f"datum: {d}")
    print(f"redeemer: {r}")
    print(f"script context: {context}")
    raise AssertionError("Failing in order to show script logs")
