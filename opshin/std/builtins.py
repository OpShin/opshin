"""
A special libary that gives direct access to UPLC built-ins
It is valid code and parts of it may be copied if not all built-ins are required by the user.
"""

from opshin.bridge import wraps_builtin
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union


@wraps_builtin
def add_integer(x: int, y: int) -> int:
    """Adds two integers and returns the result."""
    pass


@wraps_builtin
def subtract_integer(x: int, y: int) -> int:
    """Subtract fist integer by second and return the result."""
    pass


@wraps_builtin
def multiply_integer(x: int, y: int) -> int:
    """Multiply 2 integers and return the result."""
    pass


@wraps_builtin
def divide_integer(x: int, y: int) -> int:
    """Divide first integer by second and return the result."""
    pass


@wraps_builtin
def quotient_integer(x: int, y: int) -> int:
    """Quotient of first integer by second and return the result."""
    pass


@wraps_builtin
def remainder_integer(x: int, y: int) -> int:
    """Remainder of first integer by second and return the result."""
    pass


@wraps_builtin
def mod_integer(x: int, y: int) -> int:
    """Modulus of first integer by second and return the result."""
    pass


@wraps_builtin
def equals_integer(x: int, y: int) -> bool:
    """Equality between two integers."""
    pass


@wraps_builtin
def less_than_integer(x: int, y: int) -> bool:
    """Returns x < y"""
    pass


@wraps_builtin
def less_than_equals_integer(x: int, y: int) -> bool:
    """Returns x <= y."""
    pass


@wraps_builtin
def append_byte_string(x: bytes, y: bytes) -> bytes:
    """Concatenate two bytestrings."""
    pass


@wraps_builtin
def cons_byte_string(x: int, y: bytes) -> bytes:
    """Prepend a byte, represented by a natural number (Integer), to a bytestring."""
    pass


@wraps_builtin
def slice_byte_string(x: int, y: int, z: bytes) -> bytes:
    """
    Slice a bytestring using given indices (inclusive on both ends).
    The resulting bytestring is z[x:x+y].
    """
    pass


@wraps_builtin
def length_of_byte_string(x: bytes) -> int:
    """Get the length of a bytestring."""
    pass


@wraps_builtin
def index_byte_string(x: bytes, y: int) -> int:
    """Get the byte at given index from a bytestring."""
    pass


@wraps_builtin
def equals_byte_string(x: bytes, y: bytes) -> bool:
    """Returns x == y."""
    pass


@wraps_builtin
def less_than_byte_string(x: bytes, y: bytes) -> bool:
    """Returns x < y."""
    pass


@wraps_builtin
def less_than_equals_byte_string(x: bytes, y: bytes) -> bool:
    """Returns x <= y."""
    pass


@wraps_builtin
def sha2_256(x: bytes) -> bytes:
    """Hash a bytestring using SHA-256."""
    pass


@wraps_builtin
def sha3_256(x: bytes) -> bytes:
    """Hash a bytestring using SHA3-256."""
    pass


@wraps_builtin
def blake2b_256(x: bytes) -> bytes:
    """Hash a bytestring using Blake2B-256."""
    pass


@wraps_builtin
def verify_ed25519_signature(pk: bytes, m: bytes, s: bytes) -> bool:
    """Given PubKey, Message, and Signature, verify the Ed25519 signature."""
    pass


@wraps_builtin
def verify_ecdsa_secp256k1_signature(pk: bytes, m: bytes, s: bytes) -> bool:
    """Given PubKey, Message, and Signature, verify the ECDSA signature."""
    pass


@wraps_builtin
def verify_schnorr_secp256k1_signature(pk: bytes, m: bytes, s: bytes) -> bool:
    """Given PubKey, Message, and Signature, verify the Schnorr signature."""
    pass


@wraps_builtin
def append_string(x: str, y: str) -> str:
    """Concatenate two strings/texts."""
    pass


@wraps_builtin
def equals_string(x: str, y: str) -> str:
    """Returns x == y."""
    pass


@wraps_builtin
def encode_utf8(x: str) -> bytes:
    """Encode a string/text using UTF-8."""
    pass


@wraps_builtin
def decode_utf8(x: bytes) -> str:
    """Decode a string/text using UTF-8."""
    pass


@wraps_builtin
def constr_data(x: int, y: List[Anything]) -> Anything:
    """Create a datum with constructor id x and fields y."""
    pass


@wraps_builtin
def equals_data(x: Anything, y: Anything) -> bool:
    """Equality between two complex classes."""
    pass


@wraps_builtin
def serialise_data(x: Anything) -> bytes:
    """Serialize a datum into its CBOR representation."""
    pass
