#!opshin
from opshin.prelude import *

""" This contract can be parameterized at compile time with a secret value to supply for spending """


# this contract can be parameterized at compile time. Pass the parameter with the build command
#
# $ opshin build examples/smart_contracts/parameterized.py '{"int": 42}'
@dataclass()
class Parameterized(Contract):
    parameter: int

    def spend_no_datum(self, redeemer: int, _context: ScriptContext) -> None:
        assert redeemer == self.parameter, "Wrong redeemer"
