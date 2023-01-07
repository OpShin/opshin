from eopsin.prelude import *


def validator(datum: int, redeemer: int, context: ScriptContext) -> bool:
    return datum + redeemer == 42
