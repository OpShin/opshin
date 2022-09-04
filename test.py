
from pyscc.compiler import *

program = """
def main(n: PlutusData) -> int:
    a, b = 0, 1
    for _ in range(0, int(n)):
        a, b = b, a + b
    return a
"""

print(dump(parse(program)))
prog = compile(parse(program))
print(prog)
print(prog.dumps())