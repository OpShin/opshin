
from pyscc.compiler import *

program = """
def f(n: int) -> int:
    a, b = 0, 1
    for _ in range(0, n):
        a, b = b, a + b
    return a

print("computation starts")
f(9)
print("computation finished")
"""

print(dump(parse(program)))
prog = compile(parse(program))
print(prog)
print(prog.dumps())