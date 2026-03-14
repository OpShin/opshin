#!opshin
from opshin.prelude import *


@dataclass()
class AlwaysTrue(Contract):
    def raw(self, _context: ScriptContext) -> None:
        pass
