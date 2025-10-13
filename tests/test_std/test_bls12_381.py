"""
Module to check whether bls12-381 Object-oriented interface works correctly.
"""

from tests.utils import eval_uplc_value


def test_bls12_381_g2_mul_add():
    source_code = """
from opshin.std.bls12_381 import BLS12381G2Element
from opshin.std.builtins import *

def validator(p: bytes, q: bytes) -> bytes:
    p_ = bls12_381_g2_uncompress(p)
    q_ = bls12_381_g2_uncompress(q)
    y = p_ * 2157 + q_ * 2157
    x = bls12_381_g2_compress(y)
    return x
"""
    res = eval_uplc_value(
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
