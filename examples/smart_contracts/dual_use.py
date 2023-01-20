from eopsin.prelude import *

""" This contract allows both minting and spending from its address """


def validator(_: Nothing, r: int, ctx: ScriptContext) -> None:
    assert r == 42, "Wrong redeemer"
