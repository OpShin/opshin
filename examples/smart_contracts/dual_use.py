#!opshin
from opshin.prelude import *

""" This contract allows both minting and spending from its address """


# this contract should always be called with three virtual parameters, so enable --force-three-params
#
# $ opshin build spending examples/smart_contracts/dual_use.py --force-three-params
def validator(_: Nothing, r: int, ctx: ScriptContext) -> None:
    assert r == 42, "Wrong redeemer"
