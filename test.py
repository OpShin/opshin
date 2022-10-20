
from pyscc.compiler import *

program2 = """
def main(n: PlutusData) -> int:
    a, b = 0, 1
    for _ in range(int(n)):
        a, b = b, a + b
    return a
"""
program = """
from dataclasses import dataclass

@dataclass(frozen=True)
class PlutusData:
    f1: int
    f2: str

def main(n: PlutusData) -> str:
    return n.f2
"""

# print(dump(parse(program)))
prog = compile(parse(program))
print(prog.dumps())
# print(prog.compile().dumps())