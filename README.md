
<div align="center">

<img  src="https://raw.githubusercontent.com/ImperatorLang/eopsin/c485feda7b5e7eb0d835f3ad39eed679b96aa05c/eopsin.png" width="240" />
<h1 style="text-align: center;">Eopsin</h1></br>

[![Build Status](https://app.travis-ci.com/ImperatorLang/eopsin.svg?branch=master)](https://app.travis-ci.com/ImperatorLang/eopsin)
[![PyPI version](https://badge.fury.io/py/eopsin-lang.svg)](https://pypi.org/project/eopsin-lang/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/eopsin-lang.svg)
[![PyPI - Status](https://img.shields.io/pypi/status/eopsin-lang.svg)](https://pypi.org/project/eopsin-lang/)
[![Coverage Status](https://coveralls.io/repos/github/ImperatorLang/eopsin/badge.svg?branch=master)](https://coveralls.io/github/ImperatorLang/eopsin?branch=master)

</div>

This is an implementation of smart contracts for Cardano which are written in a very strict subset of valid Python.
The general philosophy of this project is to write a compiler that 
ensure the following:

If the program compiles then:
1. it is a valid Python program
2. the output running it with python is the same as running it on-chain.

### Why eopsin?
- 100% valid Python. Leverage the existing tool stack for Python, syntax highlighting, linting, debugging, unit-testing, [property-based testing](https://hypothesis.readthedocs.io/), [verification](https://github.com/marcoeilers/nagini)
- Intuitive. Just like Python.
- Flexible. Imperative, functional, the way you want it.
- Efficient & Secure. Static type inference ensures strict typing and optimized code


### Getting Started

#### Installation

Install Python 3.8. Then run

```bash
python3 -m pip install eopsin-lang
```

#### Writing a Smart Contract

A simple contract called the "Gift Contract" verifies that only specific wallets can withdraw money.
They are authenticated by a signature.

```python3
from eopsin.prelude import *


class CancelDatum(PlutusData):
    pubkeyhash: bytes


def validator(datum: CancelDatum, redeemer: None, context: ScriptContext) -> None:
    sig_present = False
    for s in context.tx_info.signatories:
        if datum.pubkeyhash == s:
            sig_present = True
    assert sig_present
```

All contracts written in eopsin are 100% valid python.
See the `examples` directory for more.

### Compiling

Write your program in python. You may start with the content of `examples`.
Arguments to scripts are passed in as Plutus Data objects in JSON notation.

You can run any of the following commands
```bash
# Evaluate script in Python - this can be used to make sure there are no obvious errors
python3 -m eopsin eval examples/smart_contracts/sum_sc.py "{\"int\": 4}" "{\"int\": 38}" "{\"constructor\": 0, \"fields\": []}"

# Compile script to 'uplc', the Cardano Smart Contract assembly
python3 -m eopsin compile examples/smart_contracts/assert_sum.py > assert_sum.uplc
```

### Deploying

Run the following to obtain a `cardano-cli` compatible version of your smart contract:

> This requires you to install [`aiken`](https://github.com/aiken-lang/aiken)

```bash
cat examples/smart_contracts/assert_sum.py | bash scripts/python_to_plutus_via_aiken.sh > assert_sum.plutus
```

You can generate a script address from this using the official [cardano-cli](https://github.com/input-output-hk/cardano-node#using-cardano-cli)
```bash
cardano-cli address build --payment-script-file assert_sum.plutus --mainnet
```

Now you can continue and send/spend ADA with this address following [the official documentation](https://github.com/input-output-hk/cardano-node/blob/master/doc/reference/plutus/plutus-spending-script-example.md)!

### Deploying via pluto

You may alternatively use [`pluto`](https://github.com/Plutonomicon/pluto) to compile the contracts.
Beware that it might not be very fast.

```bash
cat examples/smart_contracts/assert_sum.py | bash scripts/python_to_plutus_via_pluto.sh > assert_sum.plutus
```


### The small print

_Not every valid python program is a valid smart contract_.
Not all language features of python will or can be supported.
The reasons are mainly of practical nature (i.e. we can't infer types when functions like `eval` are allowed).
Specifically, only a pure subset of python is allowed.
Further, only immutable objects may be generated.

For your program to be accepted, make sure to only make use of language constructs supported by the compiler.
You will be notified of which constructs are not supported when trying to compile.

### Name

> Eopsin (Korean: 업신; Hanja: 業神) is the goddess of the storage and wealth in Korean mythology and shamanism. 
> [...] Eopsin was believed to be a pitch-black snake that had ears. [[1]](https://en.wikipedia.org/wiki/Eopsin)

Since this project tries to merge Python (a large serpent) and Pluto/Plutus (Greek wealth gods), the name appears fitting.

## Contributing

### Architecture

This program consists of a few independent components:
1. An aggressive static type inferencer
2. Rewriting tools to simplify complex python expressions
3. A compiler from a subset of python into UPLC

### Debugging artefacts

For debugging purposes, you can also run

```bash
# Compile script to 'uplc', and evaluate the script in UPLC (for debugging purposes)
python3 -m eopsin eval_uplc examples/sum_sc.py "{\"int\": 4}" "{\"int\": 38}" "{\"constructor\": 0, \"fields\": []}"

# Compile script to 'pluto', an intermediate language (for debugging purposes)
python3 -m eopsin compile_pluto examples/sum_sc.py
```

### Sponsoring

You can sponsor the development of eopsin. Just drop me a message on social media and let me know what it is for.
