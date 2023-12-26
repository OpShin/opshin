import hypothesis
import hypothesis.strategies as hst
from hashlib import sha256, sha3_256, blake2b

from .utils import eval_uplc_value

pos_int = hst.integers(min_value=0)


@hypothesis.given(hst.binary())
def test_sha256(b: bytes):
    source_code = """
from hashlib import sha256
def validator(b: bytes) -> bytes:
    return sha256(b).digest()
"""
    res = eval_uplc_value(source_code, b)
    exp = sha256(b).digest()
    assert res == exp, "Invalid implementation of sha256"


@hypothesis.given(hst.binary())
def test_sha3_256(b: bytes):
    source_code = """
from hashlib import sha3_256
def validator(b: bytes) -> bytes:
    return sha3_256(b).digest()
"""
    res = eval_uplc_value(source_code, b)
    exp = sha3_256(b).digest()
    assert res == exp, "Invalid implementation of sha3_256"


@hypothesis.given(hst.binary())
def test_blake2b(b: bytes):
    source_code = """
from hashlib import blake2b
def validator(b: bytes) -> bytes:
    return blake2b(b).digest()
"""
    res = eval_uplc_value(source_code, b)
    # TODO this is an error in the semantics, strictly speaking
    exp = blake2b(b, digest_size=32).digest()
    assert res == exp, "Invalid implementation of blake2b"
