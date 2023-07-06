"""
A special libary that gives direct access to UPLC built-ins
It is valid code and parts of it may be copied if not all built-ins are required by the user.
"""
from opshin.bridge import wraps_builtin
from pycardano import Datum as Anything, PlutusData


@wraps_builtin
def add_integer(x: int, y: int) -> int:
    pass


@wraps_builtin
def subtract_integer(x: int, y: int) -> int:
    pass


@wraps_builtin
def multiply_integer(x: int, y: int) -> int:
    pass


@wraps_builtin
def divide_integer(x: int, y: int) -> int:
    pass


@wraps_builtin
def quotient_integer(x: int, y: int) -> int:
    pass


@wraps_builtin
def remainder_integer(x: int, y: int) -> int:
    pass


@wraps_builtin
def mod_integer(x: int, y: int) -> int:
    pass


@wraps_builtin
def equals_integer(x: int, y: int) -> bool:
    pass


@wraps_builtin
def less_than_integer(x: int, y: int) -> bool:
    pass


@wraps_builtin
def less_than_equals_integer(x: int, y: int) -> bool:
    pass


@wraps_builtin
def append_byte_string(x: bytes, y: bytes) -> bytes:
    pass


@wraps_builtin
def cons_byte_string(x: int, y: bytes) -> bytes:
    pass


@wraps_builtin
def slice_byte_string(x: int, y: int, z: bytes) -> bytes:
    pass


@wraps_builtin
def length_of_byte_string(x: bytes) -> int:
    pass


@wraps_builtin
def index_byte_string(x: bytes, y: int) -> int:
    pass


@wraps_builtin
def equals_byte_string(x: bytes, y: bytes) -> bool:
    pass


@wraps_builtin
def less_than_byte_string(x: bytes, y: bytes) -> bool:
    pass


@wraps_builtin
def less_than_equals_byte_string(x: bytes, y: bytes) -> bool:
    pass


@wraps_builtin
def sha2_256(x: bytes) -> bytes:
    pass


@wraps_builtin
def sha3_256(x: bytes) -> bytes:
    pass


@wraps_builtin
def blake2b_256(x: bytes) -> bytes:
    pass


@wraps_builtin
def verify_ed25519_signature(pk: bytes, m: bytes, s: bytes) -> bool:
    pass


@wraps_builtin
def verify_ecdsa_secp256k1_signature(pk: bytes, m: bytes, s: bytes) -> bool:
    pass


@wraps_builtin
def verify_schnorr_secp256k1_signature(pk: bytes, m: bytes, s: bytes) -> bool:
    pass


@wraps_builtin
def append_string(x: str, y: str) -> str:
    pass


@wraps_builtin
def equals_string(x: str, y: str) -> str:
    pass


@wraps_builtin
def encode_utf8(x: str) -> bytes:
    pass


@wraps_builtin
def decode_utf8(x: bytes) -> str:
    pass


@wraps_builtin
def equals_data(x: Anything, y: Anything) -> bool:
    pass


@wraps_builtin
def serialise_data(x: Anything) -> bytes:
    pass
