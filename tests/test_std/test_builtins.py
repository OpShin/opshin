from tests.utils import eval_uplc_value

"""
Module to check whether importing builtins and executing them works correctly.
"""


def test_bls12_381_g2_uncompress():
    source_code = """
from opshin.std.bls12_381 import BLS12381G2Element
from opshin.std.builtins import *

def validator(x: bytes) -> bool:
    y = bls12_381_g2_uncompress(x)
    x_prime = bls12_381_g2_compress(y)
    return x == x_prime
"""
    res = eval_uplc_value(
        source_code,
        bytes.fromhex(
            "88138ebea766d4d1aa64dd3b5826244c32ea3fe9351f9c8d584203716dae151d14bb5d06e245c24877955c79287682ba082d077bbb2afdb1ad1d48d18e2f0c56b001bce207801adfa9fd451fc59d56f0433b02f921ba5a272c58c06536291d07"
        ),
    )
    assert res == True
