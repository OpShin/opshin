import dataclasses
import json
from pathlib import Path
from typing import Union

from pycardano import PlutusV2Script

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


def load_contract(contract_path: Union[Path, str]) -> ScriptArtifacts:
    """
    Load a contract from a file or directory and generate the artifacts
    """
    if isinstance(contract_path, str):
        contract_path = Path(contract_path)
    if contract_path.is_dir():
        contract_candidates = list(contract_path.iterdir())
    elif contract_path.is_file():
        contract_candidates = [contract_path]
    else:
        raise ValueError(
            f"Invalid contract path, is neither file nor directory: {contract_path}"
        )
    contract_cbor = None
    for contract_file in contract_candidates:
        with contract_file.open("r") as f:
            contract_content = f.read()
        # could be a singly wrapped cbor hex
        try:
            # try to unwrap to see if it is cbor
            contract_cbor_unwrapped = cbor2.loads(bytes.fromhex(contract_content))
            contract_cbor = bytes.fromhex(contract_content)
            # if we can unwrap again, its doubly wrapped
            try:
                cbor2.loads(contract_cbor_unwrapped)
                contract_cbor = contract_cbor_unwrapped
            except ValueError:
                pass
            break
        except ValueError:
            pass
        # could be a plutus json
        try:
            contract = json.loads(contract_content)
            contract_cbor = cbor2.loads(bytes.fromhex(contract["cborHex"]))
        except (ValueError, KeyError):
            pass
        # could be uplc
        try:
            contract_ast = uplc.parse(contract_content)
            contract_cbor = uplc.flatten(contract_ast)
        except:
            pass
    if contract_cbor is None:
        raise ValueError(f"Could not load contract from file {contract_path}")
    return generate_artifacts(PlutusV2Script(contract_cbor))
