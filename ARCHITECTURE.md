# Architectural Decisions

On a high level, OpShin works based on a few things:

 - We can map the basic Python types `str`, `int`, `bytes` etc nicely to basic types in the underlying "assembly language" [UPLC](https://blog.hachi.one/post/an-introduction-to-plutus-core/)
 - We can infer all types of the Python AST nodes for a well chosen subset of Python using [a strict type inferencer](https://legacy.python.org/workshops/2000-01/proceedings/papers/aycock/aycock.html#CITEaiken)
 - We can map the imperative language Python to functional UPLC using [the Y combinator](https://matt.might.net/articles/compiling-up-to-lambda-calculus/)
 - We can store variables in [statemonads](https://wiki.haskell.org/State_Monad) for mutability implicitly (i.e. such that the user does not have to worry about it anymore, in contrast to how it is done in Haskell)

This results effectively in a compiler that transforms Python code into UPLC, which can be executed on-chain.

Note that this brings

1. accessibility: All users of Python (~50% of programmers) can now read (and write) smart contracts!
2. performance: We compile instead of interpreting, the latter being the main reason for CPython being slow, but [Python is not inherently slow](https://www.pypy.org/) and [OpShin is not either](https://github.com/OpShin/plutus-bench)
 
## Architecture

This program consists of a few independent components:

1. An aggressive static type inferencer
2. Rewriting tools to simplify complex python expressions
3. A compiler from a subset of Python into UPLC, which is itself divided in two steps
   1. Compilation from Python into [pluthon](https://github.com/OpShin/pluthon), an intermediate language based on pluto
   2. Compilation from pluthon into [UPLC](https://github.com/OpShin/uplc), the final "assembly language" of the Cardano Blockchain

In particular, these steps are performed in the following modules:

- type inference: `opshin.type_inference`
- compilation (python -> pluthon): `opshin.compiler`
- building (deriving script address and convenience functions): `opshin.builder`

There are futher `opshin.rewrite` and `opshin.optimize` which perform various rewriting steps (that remove complexity from python source code) and optimizations (that make sure performance is even better).

## Memory

Memory is represented in a statemonad.
The memory monad has bytestrings as variable names and maps these to atomic values (local vars).
The byte strings are local variable names and map directly to respective UPLC values.
This means that wrong applications of functions to variables may cause uncatchable errors.
The strict typing system tries to avoid such issues.

## Objects

In general, python objects are represented by equivalent Plutus Data counterparts.
Therefore, only an immutable subset of python values is allowed and Union types must have distinct constructors to be distinguishable.
No subtyping is possible.

## Execution / ABI

Every evaluated part of the python expression tree results in a statemonad of local variables.
The exception are functions:

The ABI for functions is that they are a lambda function with `n + 1` arguments:
 - the original `n` arguments of the function
 - `s`: the statemonad of the callee 
   - this may or may not include the defined function, as the name might be overwritten
   - functions that need to be recursive should bind to themselves before being exposed to the python ABI

They should return only one value, their return value.
As a direct consequence, opshin may only allow a pure subset of python (except for `print`).
Arguments are fully evaluated, they do not require another application of the statemonad.

Note that this means the function has access to all variables defined in the surrounding code _at the time of the function being called_.
This is consistent with the way it is done in python.


The python atomic types map to the UPLC builtin equivalents.
They are cast from and to plutus equivalents when passed into the validator and returned from it.

Exceptions and Catching are not supported.
Errors may occur and are not recoverable.

## Parameterized Scripts

Plutus scripts can be parameterized, meaning that the compiled UPLC contract
allows applying additional parameters until it accepts datums/redeemers.
Defining a parameterized script with opshin is straightforward -
define a validator with more than the necessary amount of parameters.
The last two/three parameters are always considered the (datum/)redeemer/script context parameters.
If you intend on writing a parameterized minting script with only two parameters,
make sure that the (Minting/Spending double functionality is set correctly)[#minting-policy---spending-validator-double-function].

The remaining parameters can be applied to the program to form a new UPLC program
that is the contract obtained by parameterization.

One important question is how to reconstruct these parameters for example
when simulating the contract in the original language.
There is no _general_ way of reconstruct these parameters from the on-chain UPLC.
However, _well-behaved_ instantiations should result in UPLC code of the following form

```uplc
[(...) param_n param_n-1 ... param_2 param_1]
```

This can be used to reconstruct the parameters that are supplied in the first positions
of the higher level validator using this mapping.
Parameters are always in the form of Data objects

- int: iData x -> x
- bytes: bData x -> x
- str: bData x -> x.encode("utf8")
- unit: _ -> None
- X(PlutusData): x -> x

The double minting functionality is _not_ affected by parameterization.

You can compile a contract with initialized parameters like this (in the same way you would evaluate a contract with parameters)

```bash
opshin compile contract.py "param_1_json_value" ... "param_n_json_value"
```

## Minting policy - Spending validator double function

> The ugly hack

Usually, minting policies on cardano take only 2 arguments: a redeemer and the script context.
Spending validators take 3 arguments: a datum locked at the utxo to spend, a redeemer and the script context.
With opshin, minting policies also take 3 arguments: a unit, a redeemer and the script context.
This has a number of benefits:

 - both types of validators have the same signature, being less confusing for developers to write
 - validators can double function as both minting policy and script - where they know the hash of both

This comes at the cost of an ugly hack.
Generally, all validator functions `v` are wrapped in a short script that takes two arguments `a0` and `a1`.
It checks whether `a1` is a ScriptContext by checking if it is PlutusData and has constructor id `0`.
If so, `v({6:[]}, a0, a1)` is executed and returned,
where `{6:[]}` represents an object of type `Nothing` as defined in the prelude.
If not, `v(a0, a1)` is executed (the first two arguments being bound to the function)
and returned, expecting as only argument the remaining script context.

The single only drawback of this approach is that the second argument to a validator
may never be PlutusData with constructor id 0 - which is bearable.

In order to benefit from the double functionality, make sure to compile the code with the flag `--force-three-params`.

```bash
opshin compile examples/smart_contracts/wrapped_token.py --force-three-params
```