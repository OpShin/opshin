import json
from sys import stdin
import cbor2

inp = stdin.buffer.read()
cbor = cbor2.dumps(inp)
cbor_hex = cbor.hex()
d = {
    "type": "PlutusScriptV1",
    "description": "A Smart Contract written in Eopsin",
    "cborHex": cbor_hex,
}
print(json.dumps(d))
