#!/usr/bin/env -S opshin eval spending
from opshin.prelude import *
from opshin.std.integrity import check_integrity


@dataclass
class WithdrawDatum(PlutusData):
    CONSTR_ID = 0
    pubkeyhash: PubKeyHash


def validator(context: ScriptContext) -> None:
    datum: WithdrawDatum = own_datum(context)
    # check that the datum has correct structure (recommended for user inputs)
    # can be omitted if the datum can not make its way into a permanent script state (i.e., not stored in an output)
    check_integrity(datum)
    sig_present = datum.pubkeyhash in context.transaction.signatories
    assert (
        sig_present
    ), f"Required signature missing, expected {datum.pubkeyhash.hex()} but got {[s.hex() for s in context.transaction.signatories]}"
