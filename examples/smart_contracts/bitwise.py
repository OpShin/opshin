#!opshin
from opshin.prelude import *
from opshin.std.integrity import check_integrity
from opshin.std.math import *


def validator(context: ScriptContext) -> None:
    """
    A contract that checks whether the bitwise AND of the datum and redeemer is zero.
    """
    maybe_datum = own_datum(context)
    # it is possible that no datum is attached (new in PlutusV3)
    if isinstance(maybe_datum, NoOutputDatum):
        # in that case, no datum was attached and we accept the transaction
        return
    else:
        datum: int = maybe_datum.datum
        # In plutus v3, the redeemer is in the script context
        redeemer: int = context.redeemer
        datum_bytes = bytes_big_from_unsigned_int(datum)
        redeemer_bytes = bytes_big_from_unsigned_int(redeemer)
        # compute the bitwise XOR of the two byte arrays
        and_bytes = xor_byte_string(True, datum_bytes, redeemer_bytes)
        and_int = unsigned_int_from_bytes_big(and_bytes)
        assert and_int == 0, f"Expected bitwise XOR to be zero, but got {and_int}"
