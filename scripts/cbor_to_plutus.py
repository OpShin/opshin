import json
from sys import stdin
import cbor2
from eopsin import __version__

inp = stdin.buffer.read()
cbor = cbor2.dumps(inp)
cbor_hex = cbor.hex()
d = {
    "type": "PlutusScriptV2",
    "description": f"Eopsin {__version__} Smart Contract",
    "cborHex": cbor_hex,
}
print(json.dumps(d))
