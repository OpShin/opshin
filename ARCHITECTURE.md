# Architectural Decisions

On a high level, OpShin works based on a few things:

 - We can map the basic Python types `str`, `int`, `bytes` etc nicely to basic types in the underlying "assembly language" [UPLC](https://blog.hachi.one/post/an-introduction-to-plutus-core/)
 - We can infer all types of the Python AST nodes for a well chosen subset of Python using [a strict type inferencer](https://legacy.Python.org/workshops/2000-01/proceedings/papers/aycock/aycock.html#CITEaiken)
 - We can map the imperative language Python to functional UPLC using [the Y combinator](https://matt.might.net/articles/compiling-up-to-lambda-calculus/)
 - We can store variables in [statemonads](https://wiki.haskell.org/State_Monad) for mutability implicitly (i.e. such that the user does not have to worry about it anymore, in contrast to how it is done in Haskell)

This results effectively in a compiler that transforms Python code into UPLC, which can be executed on-chain.

Note that this brings

1. accessibility: All users of Python (~50% of programmers) can now read (and write) smart contracts!
2. performance: We compile instead of interpreting, the latter being the main reason for CPython being slow, but [Python is not inherently slow](https://www.pypy.org/) and [OpShin is not either](https://github.com/OpShin/plutus-bench)

## Notes on the validator function and types

Parameters to the validator (on- and off-chain) are always expected in the form of Data objects and will be converted to uplc native parameters upon being passed in (see the mapping below).
Data objects are not translated to uplc native values to save execution time.
Data objects are neither type checked. You need to make sure that the validator does not become vulnerable due to potentially invalid parameters.

The `isinstance` function does only check that the constructor id of the Data object matches the expected one.
It does not check that the number or type of data fields is correct nor does it check that no additional or invalid fields are provided.
Checking this is the responsibility of the writer of the validator.
The reason for this is that the validator is executed on-chain and we want to save execution time - not everything needs to be checked in order to prevent vulnerabilities.
You should definitely check values that represent a continuing, chained state of the protocol (to prevent halting the protocol by providing a too large state)
This is especially relevant when the state may be modified by anyone rather than only the owner of the state (i.e. a user that stakes funds).
The script context never needs to be checked - it can not be controlled by anyone but the protocol.
 
## Architecture

This program consists of a few independent components:

1. An aggressive static type inferencer
2. Rewriting tools to simplify complex Python expressions
3. A compiler from a subset of Python into UPLC, which is itself divided in two steps
   1. Compilation from Python into [pluthon](https://github.com/OpShin/pluthon), an intermediate language based on pluto
   2. Compilation from pluthon into [UPLC](https://github.com/OpShin/uplc), the final "assembly language" of the Cardano Blockchain

In particular, these steps are performed in the following modules:

- type inference: `opshin.type_inference`
- compilation (Python -> pluthon): `opshin.compiler`
- building (deriving script address and convenience functions): `opshin.builder`

There are futher `opshin.rewrite` and `opshin.optimize` which perform various rewriting steps (that remove complexity from Python source code) and optimizations (that make sure performance is even better).

## Memory

Variables are stored as actual UPLC variables (without the need for a statemonad).
UPLC does not really have a concept of variables, but we can emulate them by applying
the values to a function that takes the variable name as argument.
Variable re-assignments are simply nested variable declarations, which by default
shadow the previous variable in UPLC.

Loops are directly mapped to recursive functions that take care of re-assigning all variables
that are modified in the loop body.

## Objects

In general, Python objects are represented by equivalent Plutus Data counterparts.
Therefore, only an immutable subset of Python values is allowed and Union types must have distinct constructors to be distinguishable.
No subtyping is possible.

## Execution / ABI

Every evaluated part of the Python expression tree results in a value that is returned.

Functions expect their arguments to be wrapped in a single delay statement.
Functions take the number of arguments that they are defined with plus all variables that are defined in the surrounding code and read by the function.
The order of arguments is first all variables defined in the surrounding code in alphabetical increasing order (there are no ties), then all arguments.
The exception to this rule are functions that are defined with 0 arguments and 0 read variables.
They are compiled to functions that take a single argument, which is discarded upon application.

Note that this is necessary because the function has access to all variables defined in the surrounding code _at the time of the function being called_.
This is consistent with the way it is done in Python.

Functions and expressions evaluate to a single value and hence have no side effects.
As a direct consequence, opshin may only allow a pure subset of Python (except for `print`, which has no effect on memory).

The Python atomic types map to the UPLC builtin equivalents.
They are cast from and to Plutus equivalents when passed into the validator and returned from it.
The map is as follows:
   - `int` <-> `BuiltinInteger` <-> `PlutusInteger`
   - `str` <-> `BuiltinString` <->  `PlutusByteString` (with utf8 de- and encoding)
   - `bytes` <-> `BuiltinByteString` <-> `PlutusByteString`
   - `bool` <-> `BuiltinBool` <-> `PlutusInteger` (`True` <-> `1`, `False` <-> `0`)
   - `None` <-> `BuiltinUnit` <-> `PlutusConstr(0, [])`
   - `list` <-> `BuiltinList` <-> `PlutusList`
   - `dict` <-> `BuiltinList` (of data pairs) <-> `PlutusMap`
   - all subclasses of `PlutusData` <-> `PlutusData` (identity)

Exceptions and exception catching are not supported.
The only way to throw an exception is to call `assert False` or `assert <falsey value>`.
Errors may occur and are not recoverable, they should usually print the same error string as an equivalent Python function.

## Parameterized Scripts

Plutus scripts can be parameterized, meaning that the compiled UPLC contract
allows applying additional parameters until it accepts datums/redeemers.
Defining a parameterized script with opshin is straightforward -
define a validator with more than the necessary amount of parameters.
The last two/three parameters are always considered the (datum/)redeemer/script context parameters.
If you intend on writing a parameterized minting script with only two parameters,
make sure that the [Minting/Spending double functionality is set correctly](#minting-policy---spending-validator-double-function).

The remaining parameters can be applied to the program to form a new UPLC program
that is the contract obtained by parameterization.

One important question is how to reconstruct these parameters for example
when simulating the contract in the original language.
There is no _general_ way of reconstruct these parameters from the on-chain UPLC.
However, _well-behaved_ instantiations should result in UPLC code of the following form

```uplc
[(...) param_1 param_2 ... param_n-1 param_n]
```

This can be used to reconstruct the parameters that are supplied in the first positions
of the higher level validator using this mapping.
Parameters are always in the form of Data objects and will be converted to uplc native parameters upon being passed in (see the mapping above).
The native PoS type of PlutusV3 and beyond is not used.

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