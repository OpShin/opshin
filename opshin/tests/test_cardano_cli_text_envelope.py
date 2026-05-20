import json
import tempfile

import cbor2

from opshin import PlutusContract, builder


def test_script_plutus_cbor_hex_wraps_script_cbor_for_cardano_cli():
    source_code = """
from opshin.prelude import *


def validator(_: BuiltinData, __: BuiltinData):
    pass
"""
    contract = builder._build(builder._compile(source_code))
    artifacts = PlutusContract(contract)

    with tempfile.TemporaryDirectory() as target_dir:
        artifacts.dump(target_dir)

        with open(f"{target_dir}/script.cbor") as fp:
            script_cbor = bytes.fromhex(fp.read())
        with open(f"{target_dir}/script.plutus") as fp:
            script_plutus = json.load(fp)

    assert script_plutus["cborHex"] == cbor2.dumps(script_cbor).hex()
    assert cbor2.loads(bytes.fromhex(script_plutus["cborHex"])) == script_cbor
