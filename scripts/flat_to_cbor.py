from sys import stdin, stdout
import cbor2

inp = stdin.buffer.read()
cbor = cbor2.dumps(inp)
stdout.buffer.write(cbor)
