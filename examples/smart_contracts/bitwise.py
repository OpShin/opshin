#!opshin
from opshin.prelude import *
from opshin.std.math import *


def validator(datum: int, redeemer: int, context: ScriptContext) -> None:
    """
    A contract that checks whether the bitwise AND of the datum and redeemer is zero.
    """
    datum_bytes = bytes_big_from_unsigned_int(datum)
    redeemer_bytes = bytes_big_from_unsigned_int(redeemer)
    # compute the bitwise AND of the two byte arrays
    and_bytes = and_bytestring(datum_bytes, redeemer_bytes)
    and_int = unsigned_int_from_bytes_big(and_bytes)
    assert and_int == 0, f"Expected bitwise AND to be zero, but got {and_int}"
