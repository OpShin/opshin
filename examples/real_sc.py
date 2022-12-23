from pyscc.prelude import *

class CancelDatum(PlutusData):
    CONSTR_ID = 0
    pubkeyhash: bytes

class CancelRedeemer(PlutusData):
    CONSTR_ID = 0

def validator(datum: CancelDatum, redeemer: CancelRedeemer, context: ScriptContext):
    return datum.pubkeyhash in context.tx_info.signatories