from sys import stdout

hex = input().strip()
stdout.buffer.write(bytes.fromhex(hex))
