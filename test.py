
from pyscc.compiler import *

program2 = """
def main(n: PlutusData) -> int:
    a, b = 0, 1
    for _ in range(int(n)):
        a, b = b, a + b
    return a
"""
program = """
def main(n: PlutusData) -> None:
    a, b = 0, int(n)
    if b < 5:
        print("add")
        a += 5
    else:
        print("sub")
        a -= b
    return a
"""

# print(dump(parse(program)))
prog = compile(parse(program))
print(prog.dumps())
# print(prog.compile().dumps())