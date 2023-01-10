from eopsin.prelude import *


def validator(datum: int, redeemer: int, context: ScriptContext) -> None:
    assert datum + redeemer == 42
