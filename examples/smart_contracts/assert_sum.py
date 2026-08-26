#!opshin
from opshin.prelude import *


@dataclass()
class AssertSum(Contract):
    def spend_with_datum(
        self, datum: int, redeemer: int, _context: ScriptContext
    ) -> None:
        assert (
            datum + redeemer == 42
        ), f"Expected datum and redeemer to sum to 42, but they sum to {datum + redeemer}"
