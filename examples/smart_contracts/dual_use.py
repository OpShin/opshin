#!opshin
from opshin.prelude import *

""" This contract allows both minting and spending from its address """


# this contract should always be built with three virtual parameters, setting --force-three-params.
# For example:
# $ opshin build spending examples/smart_contracts/dual_use.py --force-three-params
# Note that dual-use contracts need to have a Union[Nothing] datum (it is nothing for anything but spending) and a non-0 constructor for redeemers
def validator(_: Nothing, r: int, ctx: ScriptContext) -> None:
    assert r == 42, "Wrong redeemer"
