from eopsin.prelude import *


class CancelDatum(PlutusData):
    CONSTR_ID = 0
    pubkeyhash: bytes


class CancelRedeemer(PlutusData):
    CONSTR_ID = 0


def validator(
    datum: CancelDatum, redeemer: CancelRedeemer, context: ScriptContext
) -> bool:
    res = False
    for s in context.tx_info.signatories:
        if datum.pubkeyhash == s.value:
            res = True
    return res
