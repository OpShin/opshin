import dataclasses
import json

from . import __version__, compiler

import uplc.ast
from uplc import flatten
import cbor2
import pycardano

from .util import datum_to_cbor


@dataclasses.dataclass
class ScriptArtifacts:
    cbor_hex: str
    plutus_json: str
    mainnet_addr: str
    testnet_addr: str
    policy_id: str


def build(
    contract_file: str,
    *args: pycardano.Datum,
    force_three_params=False,
    validator_function_name="validator",
):
    """
    Expects a python module and returns the build artifacts from compiling it
    """
    with open(contract_file) as f:
        source_code = f.read()

    source_ast = compiler.parse(source_code, filename=contract_file)
    code = compiler.compile(
        source_ast, filename=contract_file, force_three_params=force_three_params
    )
    code = code.compile()

    # apply parameters from the command line to the contract (instantiates parameterized contract!)
    code = code.term
    # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
    for d in args:
        code = uplc.ast.Apply(code, uplc.ast.data_from_cbor(datum_to_cbor(d)))
    code = uplc.ast.Program((1, 0, 0), code)
    return _build(code)


def _build(contract: uplc.ast.Program):
    # create cbor file for use with pycardano/lucid
    cbor = flatten(contract)
    return pycardano.PlutusV2Script(cbor)


def generate_artifacts(contract: pycardano.PlutusV2Script):
    cbor_hex = contract.hex()
    # double wrap
    cbor_wrapped = cbor2.dumps(contract)
    cbor_wrapped_hex = cbor_wrapped.hex()
    # create plutus file
    d = {
        "type": "PlutusScriptV2",
        "description": f"opshin {__version__} Smart Contract",
        "cborHex": cbor_wrapped_hex,
    }
    plutus_json = json.dumps(d, indent=2)
    script_hash = pycardano.plutus_script_hash(pycardano.PlutusV2Script(contract))
    policy_id = script_hash.to_primitive().hex()
    # generate policy ids
    addr_mainnet = pycardano.Address(
        script_hash, network=pycardano.Network.MAINNET
    ).encode()
    # generate addresses
    addr_testnet = pycardano.Address(
        script_hash, network=pycardano.Network.TESTNET
    ).encode()
    return ScriptArtifacts(
        cbor_hex,
        plutus_json,
        addr_mainnet,
        addr_testnet,
        policy_id,
    )
