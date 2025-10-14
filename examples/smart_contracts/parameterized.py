#!opshin
from opshin.prelude import *

""" This contract can be parameterized at compile time with a secret value to supply for spending """


# this contract can be parameterized at compile time. Pass the parameter with the build command
#
# $ opshin build examples/smart_contracts/parameterized.py '{"int": 42}'
def validator(ctx: ScriptContext) -> None:
    parameter: int = own_datum_unsafe(ctx)
    r: int = ctx.redeemer
    assert r == parameter, "Wrong redeemer"
