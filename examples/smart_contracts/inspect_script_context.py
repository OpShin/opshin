#!opshin
from opshin.prelude import *


def validator(context: ScriptContext):
    print(context.to_cbor())
