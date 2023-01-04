The general concept is as follows:

## Execution / ABI

Every evaluated part of the python expression tree results in a statemonad of local variables.
As a consequence, eopsin may only allow a pure subset of python.
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