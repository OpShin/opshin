The general concept is as follows:



## Execution / ABI

Every evaluated part of the python expression tree results in a tuple of
- state flag (0 = continue, 1 = computation stopped normally, 2 = error occurred)
- statemonad
- return value / exception state, depending on the state flag

Functions are always passed the statemonad as first argument.
In a return value, the state flag is only relevant if set to 2.

## Memory

Memory is represented in a statemonad.
The statemonad is a natural number (the current size of allocated heap) and a nested (lambda x: if x == y then z else f(x)) comparison.
It consists of two parts conceptually.
One part has natural numbers (pointers) as variable names and maps these numbers to atomic values.
The other part has bytestrings as variable names and maps these to atomic values.
The byte strings are local variable names and map directly to respective pointers or atomic values.
Arrays and objects may be represented by consecutive natural number allocationss in the pointer part of the statemonad.

## Objects

In general, every python object is wrapped with a thin mapping from attribute/method names to
constants/lambda functions that evaluate to the equivalent value if passed "self".

Inside the code we assume every object to be wrapped and can hence translate everything to self(attributename).

In that sense, every object is a statemonad again.

In general, subtyping is not supported in the sense that isinstance/etc do not check for subtyping relationships.
This also means that Exception handling does only work with "Exception" as catch type.