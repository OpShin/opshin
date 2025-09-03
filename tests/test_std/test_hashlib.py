import hypothesis
import hypothesis.strategies as hst
from hashlib import sha256, sha3_256, blake2b

from opshin import builder
from tests.utils import eval_uplc_value

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


@hypothesis.given(hst.binary())
def test_sha256_rename(b: bytes):
    source_code = """
from hashlib import sha256 as hsh
def validator(b: bytes) -> bytes:
    return hsh(b).digest()
"""
    res = eval_uplc_value(source_code, b)
    exp = sha256(b).digest()
    assert res == exp, "Invalid implementation of sha256"


def test_sha256_rename_conflict():
    source_code = """
from hashlib import sha256 as hsh
def validator(b: bytes) -> bytes:
    x = hsh(b).digest()
    hsh = x + b"hello"
    return hsh
"""
    try:
        builder._compile(source_code)
        assert False, "Expected an error due to import conflict"
    except Exception as e:
        assert (
            "import" in str(e).lower() and "hash" in str(e).lower()
        ), "Expected a hint about import conflict"


def test_hashlib_import_all():
    from opshin.std.hashlib import sha256, sha3_256, blake2b
