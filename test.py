
from pyscc.compiler import *

program = """
def foo(a: int) -> int:
    return a

for a in range(4):
    print("a")

a = 1 + 4
foo(a)
print("hi")
"""

print(dump(parse(program)))
prog = compile(parse(program))
print(prog)
print(prog.dumps())