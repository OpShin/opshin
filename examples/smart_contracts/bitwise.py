#!opshin
from opshin.prelude import *
from opshin.std.math import *


@dataclass()
class Contract:
    def spend(
        self, datum: Union[int, NoOutputDatum], redeemer: int, _context: ScriptContext
    ) -> None:
        """
        A contract that checks whether the bitwise AND of the datum and redeemer is zero.
        """
        if isinstance(datum, NoOutputDatum):
            return
        datum_bytes = bytes_big_from_unsigned_int(datum)
        redeemer_bytes = bytes_big_from_unsigned_int(redeemer)
        # compute the bitwise XOR of the two byte arrays
        and_bytes = xor_byte_string(True, datum_bytes, redeemer_bytes)
        and_int = unsigned_int_from_bytes_big(and_bytes)
        assert and_int == 0, f"Expected bitwise XOR to be zero, but got {and_int}"
