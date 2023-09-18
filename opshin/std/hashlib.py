"""
A std library that imports all valid hash functions from the builtin python hashlib library:
If you want to have all hash functions in scope, simply add `from opshin.std.hashlib import *` to the top of you python file.
"""

from hashlib import sha256, sha3_256, blake2b
