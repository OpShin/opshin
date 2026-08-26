#!opshin
from opshin.prelude import *


# this validator will print the datum, redeemer and script context passed from the node in a readable format
@dataclass()
class InspectScriptContext(Contract):
    def raw(self, context: ScriptContext) -> None:
        print(f"script context (CBOR hex): {context.to_cbor().hex()}")
        print(f"script context (native): {context}")

        assert False, "Failing in order to show script logs"
