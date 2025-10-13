"""
A special library that gives direct access to UPLC built-ins
It is valid code and parts of it may be copied if not all built-ins are required by the user.
"""

from opshin.bridge import wraps_builtin
from pycardano import Datum as Anything, PlutusData
from typing import Dict, List, Union
from opshin.std.bls12_381 import (
    BLS12381G1Element,
    BLS12381G2Element,
    BLS12381MillerLoopResult,
)


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


@wraps_builtin
def bls12_381_g1_uncompress(a: bytes) -> BLS12381G1Element:
    """Uncompress an element of the G1 group in BLS12_381 from its binary representation."""
    pass


@wraps_builtin
def bls12_381_g1_compress(a: BLS12381G1Element) -> bytes:
    """Compress an element of the G1 group in BLS12_381 into its binary representation."""
    pass


@wraps_builtin
def bls12_381_g1_add(a: BLS12381G1Element, b: BLS12381G1Element) -> BLS12381G1Element:
    """Adds two elements of the G1 group in BLS12_381"""
    pass


@wraps_builtin
def bls12_381_g1_neg(a: BLS12381G1Element) -> BLS12381G1Element:
    """Negate an element of the G1 group in BLS12_381."""
    pass


@wraps_builtin
def bls12_381_g1_scalar_mul(a: int, b: BLS12381G1Element) -> BLS12381G1Element:
    """Multiply an element of the G1 group in BLS12_381 with a scalar integer"""
    pass


@wraps_builtin
def bls12_381_g1_hash_to_group(a: bytes, b: bytes) -> BLS12381G1Element:
    """Hash two bytestrings into the G1 group in BLS12_381."""


@wraps_builtin
def bls12_381_g1_equal(a: BLS12381G1Element, b: BLS12381G1Element) -> bool:
    """Checks two elements of the G1 group in BLS12_381 for equality."""
    pass


@wraps_builtin
def bls12_381_g2_uncompress(a: bytes) -> BLS12381G2Element:
    """Uncompress an element of the G2 group in BLS12_381 from its binary representation."""
    pass


@wraps_builtin
def bls12_381_g2_compress(a: BLS12381G2Element) -> bytes:
    """Compress an element of the G2 group in BLS12_381 into its binary representation."""
    pass


@wraps_builtin
def bls12_381_g2_add(a: BLS12381G1Element, b: BLS12381G1Element) -> BLS12381G1Element:
    """Adds two elements of the G1 group in BLS12_381"""
    pass


@wraps_builtin
def bls12_381_g2_neg(a: BLS12381G1Element) -> BLS12381G1Element:
    """Negate an element of the G1 group in BLS12_381."""
    pass


@wraps_builtin
def bls12_381_g2_scalar_mul(a: int, b: BLS12381G1Element) -> BLS12381G1Element:
    """Multiply an element of the G1 group in BLS12_381 with a scalar integer"""
    pass


@wraps_builtin
def bls12_381_g2_hash_to_group(a: bytes, b: bytes) -> BLS12381G1Element:
    """Hash two bytestrings into the G1 group in BLS12_381."""


@wraps_builtin
def bls12_381_g2_equal(a: BLS12381G2Element, b: BLS12381G2Element) -> bool:
    """Checks two elements of the G2 group in BLS12_381 for equality."""
    pass


@wraps_builtin
def bls12_381_miller_loop(
    a: BLS12381G1Element, b: BLS12381G2Element
) -> BLS12381MillerLoopResult:
    """Computes the Miller Loop based on G1 and G2 group elements from BLS12_381."""
    pass


@wraps_builtin
def bls12_381_mul_ml_result(
    a: BLS12381MillerLoopResult, b: BLS12381MillerLoopResult
) -> BLS12381MillerLoopResult:
    """Multiplies two Miller Loop results in BLS12_381."""
    pass


@wraps_builtin
def bls12_381_final_verify(
    a: BLS12381MillerLoopResult, b: BLS12381MillerLoopResult
) -> bool:
    """Verifies two Miller Loop results in BLS12_381."""
    pass


@wraps_builtin
def keccak_256(a: bytes) -> bytes:
    """Compute the Keccak 256 bit hash of a bytestring."""
    pass


@wraps_builtin
def blake2b_224(a: bytes) -> bytes:
    """Compute the Blake 2b 224 bit hash of a bytestring."""
    pass


@wraps_builtin
def integer_to_byte_string(big_endian: bool, width: int, val: int) -> bytes:
    """Returns the integer represented by a bytestring.
    Width controls the number of bytes used. If width is 0, the minimum number of bytes is used.
    Big_endian controls the endianness."""
    pass


@wraps_builtin
def byte_string_to_integer(big_endian: bool, a: bytes) -> int:
    """Returns the representation of an integer as a bytestring. Undoes integer_to_byte_string."""
    pass


@wraps_builtin
def and_byte_string(pad: bool, a: bytes, b: bytes) -> bytes:
    """Logical AND applied to two bytestrings. The first argument indicates whether padding semantics should be used. If this argument is False, truncation semantics are used instead."""
    pass


@wraps_builtin
def or_byte_string(pad: bool, a: bytes, b: bytes) -> bytes:
    """Returns the bitwise OR of two bytestrings, asserting they have the same length. The first argument indicates whether padding semantics should be used. If this argument is False, truncation semantics are used instead."""
    pass


@wraps_builtin
def xor_byte_string(pad: bool, a: bytes, b: bytes) -> bytes:
    """Logical XOR applied to two bytestrings. The first argument indicates whether padding semantics should be used. If this argument is False, truncation semantics are used instead."""
    pass


@wraps_builtin
def complement_byte_string(a: bytes) -> bytes:
    """Returns the bitwise NOT of a bytestring."""
    pass


@wraps_builtin
def read_bit(a: bytes, index: int) -> bool:
    """Returns the bit at given index of the binary data."""
    pass


@wraps_builtin
def write_bits(a: bytes, indices: List[int], value: bool) -> bytes:
    """Sets the bits indicated by indices in the binary data to the given value."""
    pass


@wraps_builtin
def replicate_byte(a: int, b: int) -> bytes:
    """Returns a bytestring of length a with all bytes equal to b. Maximum length is 8192."""
    pass


@wraps_builtin
def shift_byte_string(a: bytes, b: int) -> bytes:
    """Returns a bytestring shifted by b bits (left shift for b > 0, right shift by -b for b < 0)"""
    pass


@wraps_builtin
def rotate_byte_string(a: bytes, b: int) -> bytes:
    """Returns a bytestring rotated by b bits (left rotate for b > 0, right rotate by -b for b < 0)"""
    pass


@wraps_builtin
def count_set_bits(a: bytes) -> int:
    """Returns the number of set bits (bits = 1) in a bytestring."""
    pass


@wraps_builtin
def find_first_set_bit(a: bytes) -> int:
    """Returns the 0-based index of the first set bit in a bytestring."""
    pass


@wraps_builtin
def ripemd_160(a: bytes) -> bytes:
    """Returns the RIPEMD-160 hash of a bytestring."""
    pass
