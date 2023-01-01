The general concept is as follows:



## Execution

Every evaluated part of the python expression tree results in a tuple of
- statemonad
- return value
- exception state

## Memory

Memory is represented in a statemonad.
The statemonad is a natural number (the current size of allocated heap) and a nested (lambda x: if x == y then z else f(x)) comparison.
It consists of two parts conceptually.
One part has natural numbers (pointers) as variable names and maps these numbers to atomic values.
The other part has bytestrings as variable names and maps these to atomic values.
The byte strings are local variable names and map directly to respective pointers or atomic values.
Arrays and objects may be represented by consecutive natural number allocationss in the pointer part of the statemonad.

## Objects

Generally, all primitive objects are kept wrapped in `Data`, which allows distinguishing dynamic types of objects.
In addition, every object is wrapped with a thin mapping from attribute/method names to
constants/lambda functions that evaluate to the equivalent value if passed "self".

Inside the code we assume every object to be wrapped and can hence translate everything to self(attributename).

In that sense, every object is a statemonad again.