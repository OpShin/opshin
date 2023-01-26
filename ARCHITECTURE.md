The general concept is as follows:

## Execution / ABI

Every evaluated part of the python expression tree results in a statemonad of local variables.
The exception are functions:

The ABI for functions is that they are a lambda function with `n + 1` arguments:
 - the original `n` arguments of the function
 - `s`: the statemonad of the callee 
   - this may or may not include the defined function, as the name might be overwritten
   - functions that need to be recursive should bind to themselves before being exposed to the python ABI

They should return only one value, their return value.
As a direct consequence, eopsin may only allow a pure subset of python (except for `print`).
Arguments are fully evaluated, they do not require another application of the statemonad.

Note that this means the function has access to all variables defined in the surrounding code _at the time of the function being called_.
This is consistent with the way it is done in python.

The python atomic types map to the UPLC builtin equivalents.
They are cast from and to plutus equivalents when passed into the validator and returned from it.

Exceptions and Catching are not supported.

## Memory

Memory is represented in a statemonad.
The memory monad has bytestrings as variable names and maps these to atomic values (local vars).
The byte strings are local variable names and map directly to respective uplc values.
This means that wrong applications of functions to variables may cause uncatchable errors.
The strict typing system tries to avoid such issues.

## Objects

In general, python objects are represented by equivalent UPLC counterparts.
This means, only an immutable subset of python values is allows.
Also, no subtyping is allowed.

## Minting policy - Spending validator double function

> The ugly hack

Usually, minting policies on cardano take only 2 arguments: a redeemer and the script context.
Spending validators take 3 arguments: a datum locked at the utxo to spend, a redeemer and the script context.
With eopsin, minting policies also take 3 arguments: a unit, a redeemer and the script context.
This has a number of benefits:

 - both types of validators have the same signature, being less confusing for developers to write
 - validators can double function as both minting policy and script - where they know the hash of both

This comes at the cost of an ugly hack.
Generally, all validator functions `v` are wrapped in a short script that takes two arguments `a0` and `a1`.
It checks whether `a1` is a ScriptContext by checking if it is PlutusData and has constructor id `0`.
If so, `v((), a0, a1)` is executed and returned.
If not, `v(a0, a1)` is executed (the first two arguments being bound to the function)
and returned, expecting as only argument the remaining script context.

The single only drawback of this approach is that the second argument to a validator
may never be PlutusData with constructor id 0 - which is bearable.

> To make the developer aware of the fact that a script might _not_ receive a datum (in the case of minting etc)
> the signature of the Datum is Union[NoDatum, SomeDatum] (both defined in the prelude)
> This also aligns writing contracts with [CIP ??? - Maybe Datum](https://github.com/cardano-foundation/CIPs/pull/440)