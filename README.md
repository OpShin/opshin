**Py**thon **S**mart **C**ontracts for **C**ardano
==================================================

This is a prototypical implementation of smart contracts
for Cardano which are written in a subset of valid Python.
The general philosphy of this project is to write a compiler that 
ensure the following:

If the program compiles then:
1. it is a valid Python program
2. the output running it with python is the same as running it on-chain.

This specificially means that _not every valid python program is a valid smart contract_.
Not all language features of python will or can be supported.
The reasons are mainly of practical nature (i.e. we can't infer types when functions like `eval` are allowed).

For your program to be accepted, make sure to only make use of language constructs supported by the compiler.
You will be notified of which constructs are not supported when trying to compile the latest.

## Architecture

This program consists of three components:
1. An aggressive static type inferencer
2. A compiler from python into UPLC/pluto
3. The UPLC/pluto toolchain in python

## Running

Write your program in python. You may start with the `example.py`.
Then run 
```bash
python3 -m pyscc compile example.py
```

> Note: this is the final desired state. I am currently too lazy to both with setting up the module so just run `python3 compiler.py example.py`