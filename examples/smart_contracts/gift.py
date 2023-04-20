from opshin.prelude import *


@dataclass
class WithdrawDatum(PlutusData):
    pubkeyhash: bytes


def validator(datum: WithdrawDatum, redeemer: None, context: ScriptContext) -> None:
    sig_present = datum in context.tx_info.signatories
    assert sig_present, "Required signature missing"
