
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
    a = 0
    while a < 2:
        a = a + 1
    return a
"""

# print(dump(parse(program)))
prog = compile(parse(program))
# print(prog)
print(prog.dumps())