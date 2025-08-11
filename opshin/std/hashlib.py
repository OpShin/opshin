"""
A std library that imports all valid hash functions from the builtin python hashlib library:
If you want to have all hash functions in scope, simply add `from opshin.std.hashlib import *` to the top of you python file.

Use it like this:
```python
from hashlib import sha256, sha3_256, blake2b

# Now you can use the hash functions directly
sha256_hash: bytes = sha256(b"Hello, World!").digest()
sha3_256_hash: bytes = sha3_256(b"Hello, World!").digest()
blake2b_hash: bytes = blake2b(b"Hello, World!").digest()
```
"""

from hashlib import sha256, sha3_256, blake2b
