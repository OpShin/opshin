from parameterized import parameterized

from opshin.ledger.api_v3 import *


@parameterized.expand(
    [
        (
            "d8799fd8799f81d8799fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd8799fd87a9f581c4154af4452c57951a0d4e9bfd36ef809c6f49ed8a66967e51cbdc314ffd87a80ffa140a1401a002dc6c0d87b9fd87980ffd87a80ffff8081d8799fd8799fd8799f581c61299458bd6d3011669ac533b520ab07b94d7428903f61714babb582ffd87a80ffa140a1401a002b112bd87980d87a80ff1a0002b595a080a0d8799fd8799fd87a9f1b0000019667dbfac0ffd87a80ffd8799fd87a9f1b0000019667ead388ffd87980ffff80a1d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffff00a05820ffa18bad2d7b861a44b07af9df6c42b60414bf0e5279134293001aea66ead701a080d87a80d87a80ff00d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd87980ffffff"
        ),
    ]
)
def test_script_context_repr_correct(p):
    # Make sure that this parses correctly and does not throw an error
    # Note that this was extracted from a PlutusV2 invocation
    # in increasing complexity...
    ScriptContext.from_cbor(p)
