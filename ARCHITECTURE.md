The general concept is as follows:

## Execution / ABI

Every evaluated part of the python expression tree results in a statemonad of local variables.
The exception are functions:

The ABI for functions is that they are a lambda function with `n + 2` arguments:
 - `f`: the function itself
 - the original `n` arguments of the function
 - `s`: the statemonad of the callee

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