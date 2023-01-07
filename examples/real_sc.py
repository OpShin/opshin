from eopsin.prelude import *


class CancelDatum(PlutusData):
    pubkeyhash: bytes


def validator(datum: CancelDatum, redeemer: None, context: ScriptContext) -> bool:
    res = False
    for s in context.tx_info.signatories:
        if datum.pubkeyhash == s.value:
            res = True
    return res
