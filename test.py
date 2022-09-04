
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
    a = 1
    a = a + int(n)
    return a
"""

# print(dump(parse(program)))
prog = compile(parse(program))
# print(prog)
print(prog.dumps())