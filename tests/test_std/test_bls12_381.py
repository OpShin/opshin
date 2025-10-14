"""
Module to check whether bls12-381 Object-oriented interface works correctly.
"""

import importlib
import pathlib
import sys
import tempfile
import uuid
import pytest

from opshin import CompilerError
from tests.utils import eval_uplc_value


def eval_python_value(source_code: str, *args):
    """Evaluate the given source code as a Python function and return the result"""
    with tempfile.TemporaryDirectory(prefix="build") as tmpdir:
        tmp_input_file = pathlib.Path(tmpdir).joinpath(f"__tmp_opshin{uuid.uuid4()}.py")
        with tmp_input_file.open("w") as fp:
            fp.write(source_code)
        sys.path.append(str(pathlib.Path(tmp_input_file).parent.absolute()))
        try:
            sc = importlib.import_module(pathlib.Path(tmp_input_file).stem)
        except Exception as e:
            # replace the traceback with an error pointing to the input file
            raise SyntaxError(
                f"Could not import the input file as python module. Make sure the input file is valid python code. Error: {e}",
            ) from e
        sys.path.pop()
    return sc.validator(*args)


def eval_both_require_equal(source_code: str, *args):
    """Evaluate the given source code as both Python and UPLC and require equal results"""
    python_result = eval_python_value(source_code, *args)
    uplc_result = eval_uplc_value(source_code, *args)
    assert python_result == uplc_result
    return python_result


# ============================================================================
# G1 Element Tests
# ============================================================================


def test_bls12_381_g1_compress():
    """Test G1 compress method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes) -> bytes:
    p_ = bls12_381_g1_uncompress(p)
    return p_.compress()
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "950dfd33da2682260c76038dfb8bad6e84ae9d599a3c151815945ac1e6ef6b1027cd917f3907479d20d636ce437a41f5"
        ),
    )
    assert res == bytes.fromhex(
        "950dfd33da2682260c76038dfb8bad6e84ae9d599a3c151815945ac1e6ef6b1027cd917f3907479d20d636ce437a41f5"
    )


def test_bls12_381_g1_add():
    """Test G1 addition using __add__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bytes:
    p_ = bls12_381_g1_uncompress(p)
    q_ = bls12_381_g1_uncompress(q)
    result = p_ + q_
    return bls12_381_g1_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "950dfd33da2682260c76038dfb8bad6e84ae9d599a3c151815945ac1e6ef6b1027cd917f3907479d20d636ce437a41f5"
        ),
    )
    assert res == bytes.fromhex(
        "a4870e983a149bb1e7cc70fde907a2aa52302833bce4d62f679819022924e9caab52e3631d376d36d9692664b4cfbc22"
    )


def test_bls12_381_g1_sub():
    """Test G1 addition using __add__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bytes:
    p_ = bls12_381_g1_uncompress(p)
    q_ = bls12_381_g1_uncompress(q)
    result = p_ - q_
    return bls12_381_g1_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
    )
    assert res == bytes.fromhex(
        "c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    )


def test_bls12_381_g1_add_associative():
    """Test G1 addition associativity: (p + q) + r == p + (q + r)"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes, r: bytes) -> bool:
    p_ = bls12_381_g1_uncompress(p)
    q_ = bls12_381_g1_uncompress(q)
    r_ = bls12_381_g1_uncompress(r)
    left = (p_ + q_) + r_
    right = p_ + (q_ + r_)
    return left == right
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "950dfd33da2682260c76038dfb8bad6e84ae9d599a3c151815945ac1e6ef6b1027cd917f3907479d20d636ce437a41f5"
        ),
        bytes.fromhex(
            "a4870e983a149bb1e7cc70fde907a2aa52302833bce4d62f679819022924e9caab52e3631d376d36d9692664b4cfbc22"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g1_add_commutative():
    """Test G1 addition commutativity: p + q == q + p"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bool:
    p_ = bls12_381_g1_uncompress(p)
    q_ = bls12_381_g1_uncompress(q)
    return p_ + q_ == q_ + p_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "950dfd33da2682260c76038dfb8bad6e84ae9d599a3c151815945ac1e6ef6b1027cd917f3907479d20d636ce437a41f5"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g1_neg():
    """Test G1 negation using __neg__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes) -> bytes:
    p_ = bls12_381_g1_uncompress(p)
    result = -p_
    return bls12_381_g1_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
    )
    assert res == bytes.fromhex(
        "8bd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
    )


def test_bls12_381_g1_pos():
    """Test G1 preservation using unary +"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes) -> bytes:
    p_ = bls12_381_g1_uncompress(p)
    result = +p_
    return bls12_381_g1_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
    )
    assert res == bytes.fromhex(
        "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
    )


def test_bls12_381_g1_add_neg():
    """Test that p + (-p) equals zero"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, zero: bytes) -> bool:
    p_ = bls12_381_g1_uncompress(p)
    zero_ = bls12_381_g1_uncompress(zero)
    result = p_ + (-p_)
    return result == zero_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g1_scalar_mul():
    """Test G1 scalar multiplication using __mul__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, scalar: int) -> bytes:
    p_ = bls12_381_g1_uncompress(p)
    result = p_ * scalar
    return bls12_381_g1_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        44,
    )
    assert res == bytes.fromhex(
        "8d9e9f6adcea14e8d38221bb3cfe4afdcc59b86e9d3b0093c0ef8252d5d90dfc5d73c9e9d352b9a54b46d35e7ff4d58c"
    )


def test_bls12_381_g1_scalar_mul_one():
    """Test that p * 1 == p"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes) -> bool:
    p_ = bls12_381_g1_uncompress(p)
    result = p_ * 1
    return result == p_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g1_scalar_mul_zero():
    """Test that p * 0 == zero"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, zero: bytes) -> bool:
    p_ = bls12_381_g1_uncompress(p)
    zero_ = bls12_381_g1_uncompress(zero)
    result = p_ * 0
    return result == zero_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g1_scalar_mul_rmul():
    """Test reverse scalar multiplication: scalar * p"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, scalar: int) -> bytes:
    p_ = bls12_381_g1_uncompress(p)
    result = scalar * p_
    return bls12_381_g1_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        44,
    )
    assert res == bytes.fromhex(
        "8d9e9f6adcea14e8d38221bb3cfe4afdcc59b86e9d3b0093c0ef8252d5d90dfc5d73c9e9d352b9a54b46d35e7ff4d58c"
    )


def test_bls12_381_g1_equal_true():
    """Test G1 equality when elements are equal"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bool:
    p_ = bls12_381_g1_uncompress(p)
    q_ = bls12_381_g1_uncompress(q)
    return p_ == q_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g1_equal_false():
    """Test G1 equality when elements are different"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bool:
    p_ = bls12_381_g1_uncompress(p)
    q_ = bls12_381_g1_uncompress(q)
    return p_ == q_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "950dfd33da2682260c76038dfb8bad6e84ae9d599a3c151815945ac1e6ef6b1027cd917f3907479d20d636ce437a41f5"
        ),
    )
    assert bool(res) is False


def test_bls12_381_g1_hash_to_group():
    """Test G1 hash_to_group operation"""
    source_code = """
from opshin.std.builtins import *

def validator(msg: bytes, dst: bytes) -> bytes:
    result = bls12_381_g1_hash_to_group(msg, dst)
    return bls12_381_g1_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        b"abc",
        b"BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_NUL_",
    )
    assert (
        res
        == b"\x8a\xb1\xbf\xedW\xbe\xf11\xb2\x05T\x18`%M\xd5F\xa5\x92\xea\xa8m\xa3\x1f1(y+\xe5\xe0\xa7\xa8#\xcbn\x7f^K\x82\xe2\xe0\xcf\xc8N\xf8/\\\xdb"
    )


# ============================================================================
# G2 Element Tests
# ============================================================================


def test_bls12_381_g2_compress():
    """Test G2 compress method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    return p_.compress()
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
        ),
    )
    assert res == bytes.fromhex(
        "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
    )


def test_bls12_381_g2_add():
    """Test G2 addition using __add__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    q_ = bls12_381_g2_uncompress(q)
    result = p_ + q_
    return bls12_381_g2_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
        ),
    )
    assert res == bytes.fromhex(
        "b5cf6c76309d98a38950948ce6768309e2e92561762734caaaab65077e1279faff6bba6f9f21bbb3b3fa4ee55aa1332d0f4b3b9a6fa4848e0bf7ae0d38fdc1f1c1908b953ee2b47b88a595b10431acab16522d12a785e27692fc7e0ffa33be07"
    )


def test_bls12_381_g2_sub():
    """Test G2 addition using __add__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    q_ = bls12_381_g2_uncompress(q)
    result = p_ - q_
    return bls12_381_g2_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
    )
    assert res == bytes.fromhex(
        "c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    )


def test_bls12_381_g2_add_associative():
    """Test G2 addition associativity: (p + q) + r == p + (q + r)"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes, r: bytes) -> bool:
    p_ = bls12_381_g2_uncompress(p)
    q_ = bls12_381_g2_uncompress(q)
    r_ = bls12_381_g2_uncompress(r)
    left = (p_ + q_) + r_
    right = p_ + (q_ + r_)
    return left == right
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
        ),
        bytes.fromhex(
            "b5cf6c76309d98a38950948ce6768309e2e92561762734caaaab65077e1279faff6bba6f9f21bbb3b3fa4ee55aa1332d0f4b3b9a6fa4848e0bf7ae0d38fdc1f1c1908b953ee2b47b88a595b10431acab16522d12a785e27692fc7e0ffa33be07"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g2_add_commutative():
    """Test G2 addition commutativity: p + q == q + p"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bool:
    p_ = bls12_381_g2_uncompress(p)
    q_ = bls12_381_g2_uncompress(q)
    return p_ + q_ == q_ + p_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g2_neg():
    """Test G2 negation using __neg__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    result = -p_
    return bls12_381_g2_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
    )
    assert res == bytes.fromhex(
        "a310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
    )


def test_bls12_381_g2_pos():
    """Test G2 negation using __pos__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    result = +p_
    return bls12_381_g2_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
    )
    assert res == bytes.fromhex(
        "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
    )


def test_bls12_381_g2_add_neg():
    """Test that p + (-p) equals zero"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, zero: bytes) -> bool:
    p_ = bls12_381_g2_uncompress(p)
    zero_ = bls12_381_g2_uncompress(zero)
    result = p_ + (-p_)
    return result == zero_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g2_scalar_mul():
    """Test G2 scalar multiplication using __mul__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, scalar: int) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    result = p_ * scalar
    return bls12_381_g2_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        1,
    )
    assert res == bytes.fromhex(
        "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
    )


def test_bls12_381_g2_scalar_mul_rmul():
    """Test reverse scalar multiplication: scalar * p"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, scalar: int) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    result = scalar * p_
    return bls12_381_g2_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        1,
    )
    assert res == bytes.fromhex(
        "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
    )


def test_bls12_381_g2_mul_add():
    """Test combined multiplication and addition for G2"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    q_ = bls12_381_g2_uncompress(q)
    y = p_ * 2157 + q_ * 2157
    x = bls12_381_g2_compress(y)
    return x
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
        ),
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
    )
    assert res == bytes.fromhex(
        "b8a335cdbb3de744ba2b6bb3c9ad9c209a7f33a1453c2ed0460e188c1f31f185e359a62727fe1d8ba5c931d75ef644e50173e5255b62194677fb67323ce42bac5c6b1b077e682df3aabca1caee2f640db1fed0b4ad511562f7c54d84ea76debc"
    )


def test_bls12_381_g2_equal_true():
    """Test G2 equality when elements are equal"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bool:
    p_ = bls12_381_g2_uncompress(p)
    q_ = bls12_381_g2_uncompress(q)
    return p_ == q_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
    )
    assert bool(res) is True


def test_bls12_381_g2_equal_false():
    """Test G2 equality when elements are different"""
    source_code = """
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bool:
    p_ = bls12_381_g2_uncompress(p)
    q_ = bls12_381_g2_uncompress(q)
    return p_ == q_
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
        ),
    )
    assert bool(res) is False


def test_bls12_381_g2_hash_to_group():
    """Test G2 hash_to_group operation"""
    source_code = """
from opshin.std.builtins import *

def validator(msg: bytes, dst: bytes) -> bytes:
    result = bls12_381_g2_hash_to_group(msg, dst)
    return bls12_381_g2_compress(result)
"""
    res = eval_both_require_equal(
        source_code,
        b"abc",
        b"BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_",
    )
    assert (
        res
        == b'\x89\xd9w\x00-z\xfe\x01=\xeb\xf4\t\xd2\xd9_kII]\x92\xe9\x04\x87J\x9b5\xc2\xc3\x14\xcd\xf9]5\xb6\x1a\xb2\xb4!\x8c"\xff\xbb\x82\xeb,J\xee\xf6\x0e\xb3\x0c\xe51\x08|\xd5B\xcf3\xa5\x94\x07R\xf7\x1dIXK\x1cm\xb72wf\x1c\xa6\x9f%=(\xec\x8eg\xc4S\x84\xda\x8a\xf7Z,\x9cV\xa8\xffw'
    )


# ============================================================================
# Miller Loop and Pairing Tests
# ============================================================================


def test_bls12_381_miller_loop():
    """Test miller_loop pairing operation"""
    source_code = """
from opshin.std.builtins import *

def validator(p1: bytes, p2: bytes, q1: bytes, q2: bytes) -> bool:
    p1_ = bls12_381_g1_uncompress(p1)
    p2_ = bls12_381_g1_uncompress(p2)
    q1_ = bls12_381_g2_uncompress(q1)
    q2_ = bls12_381_g2_uncompress(q2)
    
    ml1 = bls12_381_miller_loop(p1_, q1_)
    ml2 = bls12_381_miller_loop(p2_, q2_)
    
    return bls12_381_final_verify(ml1, ml2)
"""
    # Test vectors for pairing check
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "950dfd33da2682260c76038dfb8bad6e84ae9d599a3c151815945ac1e6ef6b1027cd917f3907479d20d636ce437a41f5"
        ),
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
        ),
    )
    assert bool(res) is False


def test_bls12_381_miller_loop_mul():
    """Test miller_loop result multiplication using __mul__ method"""
    source_code = """
from opshin.std.builtins import *

def validator(p1: bytes, p2: bytes, q1: bytes, q2: bytes) -> bool:
    p1_ = bls12_381_g1_uncompress(p1)
    p2_ = bls12_381_g1_uncompress(p2)
    q1_ = bls12_381_g2_uncompress(q1)
    q2_ = bls12_381_g2_uncompress(q2)
    
    ml1 = bls12_381_miller_loop(p1_, q1_)
    ml2 = bls12_381_miller_loop(p2_, q2_)
    
    # Test multiplication of miller loop results
    ml_combined = ml1 * ml2
    
    # This should be equivalent to doing final_verify on the product
    return True  # Just testing that multiplication works
"""
    res = eval_both_require_equal(
        source_code,
        bytes.fromhex(
            "abd61864f519748032551e42e0ac417fd828f079454e3e3c9891c5c29ed7f10bdecc046854e3931cb7002779bd76d71f"
        ),
        bytes.fromhex(
            "950dfd33da2682260c76038dfb8bad6e84ae9d599a3c151815945ac1e6ef6b1027cd917f3907479d20d636ce437a41f5"
        ),
        bytes.fromhex(
            "8310bc97fc7ad9b1616e51226c6a521b9d7fdf03f7299833e6a208ae0399fec76045a43ceef846e0958d0cdf05cf2b1f00460ee6edd2778b413eb7c272bc5b94d12b910f8ac4eb1b55e50a93644714787417bc462349c5e0f6f357b9ac32262a"
        ),
        bytes.fromhex(
            "b0629fa1158c2d23a10413fe91d381a84d25e31d041cd0377d25828498fd02011b35893938ced97535395e4815201e67108bcd4665e0db25d602d76fa791fab706c54abf5e1a9e44b4ac1e6badf3d2ac0328f5e30be341677c8bac5dda7682f1"
        ),
    )
    assert bool(res) is True
