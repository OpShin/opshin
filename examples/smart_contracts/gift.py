#!/usr/bin/env -S opshin eval spending
from opshin.prelude import *


@dataclass
class WithdrawDatum(PlutusData):
    pubkeyhash: PubKeyHash


def validator(datum: WithdrawDatum, redeemer: None, context: ScriptContext) -> None:
    sig_present = datum.pubkeyhash in context.tx_info.signatories
    assert (
        sig_present
    ), f"Required signature missing, expected {datum.pubkeyhash.hex()} but got {[s.hex() for s in context.tx_info.signatories]}"
