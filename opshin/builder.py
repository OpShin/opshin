import copy
import dataclasses
import enum
import json
import typing
from ast import Module
from typing import Optional, Any, Union
from pathlib import Path

from pycardano import PlutusV2Script, IndefiniteList, PlutusData, Datum

from . import __version__, compiler

import uplc.ast
from uplc import flatten, ast as uplc_ast, eval as uplc_eval
import cbor2
import pycardano
from pluthon import compile as plt_compile

from .util import datum_to_cbor


class Purpose(enum.Enum):
    spending = "spending"
    minting = "minting"
    rewarding = "rewarding"
    certifying = "certifying"
    any = "any"
    lib = "lib"


@dataclasses.dataclass
class ScriptArtifacts:
    cbor_hex: str
    plutus_json: str
    mainnet_addr: str
    testnet_addr: str
    policy_id: str
    blueprint: Optional[dict] = None


def compile(
    program: Module,
    contract_filename: Optional[str] = None,
    force_three_params=False,
    validator_function_name="validator",
    remove_dead_code=True,
    constant_folding=False,
    allow_isinstance_anything=False,
    **pluto_kwargs: Any,
) -> uplc_ast.Program:
    code = compiler.compile(
        program,
        filename=contract_filename,
        force_three_params=force_three_params,
        validator_function_name=validator_function_name,
        remove_dead_code=remove_dead_code,
        constant_folding=constant_folding,
        allow_isinstance_anything=allow_isinstance_anything,
    )
    plt_code = plt_compile(code, **pluto_kwargs)
    return plt_code


def _compile(
    source_code: str,
    *args: typing.Union[pycardano.Datum, uplc_ast.Constant],
    contract_file: str = "<unknown>",
    force_three_params=False,
    validator_function_name="validator",
    optimize_patterns=True,
    remove_dead_code=True,
    constant_folding=False,
    allow_isinstance_anything=False,
):
    """
    Expects a python module and returns the build artifacts from compiling it
    """

    source_ast = compiler.parse(source_code, filename=contract_file)
    code = compile(
        source_ast,
        contract_filename=contract_file,
        force_three_params=force_three_params,
        validator_function_name=validator_function_name,
        optimize_patterns=optimize_patterns,
        remove_dead_code=remove_dead_code,
        constant_folding=constant_folding,
        allow_isinstance_anything=allow_isinstance_anything,
    )

    code = _apply_parameters(code, *args)
    return code


def build(
    contract_file: str,
    *args: typing.Union[pycardano.Datum, uplc_ast.Constant],
    force_three_params=False,
    validator_function_name="validator",
    optimize_patterns=True,
):
    """
    Expects a python module and returns the build artifacts from compiling it
    """
    with open(contract_file) as f:
        source_code = f.read()
    code = _compile(
        source_code,
        *args,
        contract_file=contract_file,
        force_three_params=force_three_params,
        validator_function_name=validator_function_name,
        optimize_patterns=optimize_patterns,
    )
    return _build(code)


def _build(contract: uplc.ast.Program):
    # create cbor file for use with pycardano/lucid
    cbor = flatten(contract)
    return pycardano.PlutusV2Script(cbor)


PURPOSE_MAP = {
    Purpose.any: {"oneOf": ["spend", "mint", "withdraw", "publish"]},
    Purpose.spending: "spend",
    Purpose.minting: "mint",
    Purpose.rewarding: "withdraw",
    Purpose.certifying: "publish",
}


def to_plutus_schema(cls: typing.Type[Datum]) -> dict:
    """
    Convert to a dictionary representing a json schema according to CIP 57 Plutus Blueprint
    Reference of the core structure:
    https://cips.cardano.org/cips/cip57/#corevocabulary

    Args:
        **kwargs: Extra key word arguments to be passed to `json.dumps()`

    Returns:
        dict: a dict representing the schema of this class.
    """
    if hasattr(cls, "__origin__") and cls.__origin__ is list:
        return {
            "dataType": "list",
            **(
                {"items": to_plutus_schema(cls.__args__[0])}
                if hasattr(cls, "__args__")
                else {}
            ),
        }
    elif hasattr(cls, "__origin__") and cls.__origin__ is dict:
        return {
            "dataType": "map",
            **(
                {
                    "keys": to_plutus_schema(cls.__args__[0]),
                    "values": to_plutus_schema(cls.__args__[1]),
                }
                if hasattr(cls, "__args__")
                else {}
            ),
        }
    elif hasattr(cls, "__origin__") and cls.__origin__ is Union:
        return {
            "anyOf": [to_plutus_schema(t) for t in cls.__args__]
            if hasattr(cls, "__args__")
            else []
        }
    elif issubclass(cls, PlutusData):
        fields = []
        for field_value in cls.__dataclass_fields__.values():
            if field_value.name == "CONSTR_ID":
                continue
            field_schema = to_plutus_schema(field_value.type)
            field_schema["title"] = field_value.name
            fields.append(field_schema)
        return {
            "dataType": "constructor",
            "index": cls.CONSTR_ID,
            "fields": fields,
            "title": cls.__name__,
        }
    elif issubclass(cls, bytes):
        return {"dataType": "bytes"}
    elif issubclass(cls, int):
        return {"dataType": "integer"}
    elif issubclass(cls, IndefiniteList) or issubclass(cls, list):
        return {"dataType": "list"}
    else:
        return {}


def generate_artifacts(
    contract: pycardano.PlutusV2Script,
    datum_type: Optional[typing.Tuple[str, typing.Type[Datum]]] = None,
    redeemer_type: Optional[typing.Tuple[str, typing.Type[Datum]]] = None,
    parameter_types: typing.Iterable[typing.Tuple[str, typing.Type[Datum]]] = (),
    purpose: typing.Iterable[Purpose] = (Purpose.any,),
    version: str = "1.0.0",
    title: str = "validator",
    description: str = f"opshin {__version__} Smart Contract",
    license: Optional[str] = None,
) -> ScriptArtifacts:
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

    # generate plutus blueprint
    blueprint = {
        "$schema": "https://cips.cardano.org/cips/cip57/schemas/plutus-blueprint.json",
        "$id": "https://github.com/aiken-lang/aiken/blob/main/examples/hello_world/plutus.json",
        "$vocabulary": {
            "https://json-schema.org/draft/2020-12/vocab/core": True,
            "https://json-schema.org/draft/2020-12/vocab/applicator": True,
            "https://json-schema.org/draft/2020-12/vocab/validation": True,
            "https://cips.cardano.org/cips/cip57": True,
        },
        "preamble": {
            "version": version,
            "plutusVersion": "v2",
            "description": description,
            "title": title,
            **({"license": license} if license is not None else {}),
        },
        "validators": [
            {
                "title": title,
                **(
                    {
                        "datum": {
                            "title": datum_type[0],
                            "purpose": PURPOSE_MAP[Purpose.spending],
                            "schema": to_plutus_schema(datum_type[1]),
                        }
                    }
                    if datum_type is not None
                    else {}
                ),
                "redeemer": {
                    "title": redeemer_type[0],
                    "purpose": {"oneOf": [PURPOSE_MAP[p] for p in purpose]},
                    "schema": to_plutus_schema(redeemer_type[1]),
                }
                if redeemer_type is not None
                else {},
                **(
                    {
                        "parameters": [
                            {
                                "title": t[0],
                                "purpose": PURPOSE_MAP[Purpose.spending],
                                "schema": to_plutus_schema(t[1]),
                            }
                            for t in parameter_types
                        ]
                    }
                    if parameter_types
                    else {}
                ),
                "compiledCode": cbor_hex,
                "hash": policy_id,
            },
        ],
    }

    return ScriptArtifacts(
        cbor_hex,
        plutus_json,
        addr_mainnet,
        addr_testnet,
        policy_id,
        blueprint,
    )


def apply_parameters(script: PlutusV2Script, *args: pycardano.Datum):
    """
    Expects a plutus script (compiled) and returns the build artifacts from applying parameters to it
    """
    return generate_artifacts(_build(_apply_parameters(uplc.unflatten(script), *args)))


def apply_blueprint_parameters(validatorBlueprint: dict, *args: pycardano.Datum):
    """
    Expects a plutus validator blueprint (one of the elements in the list `validator`) and returns the new validator blueprint from applying parameters to it
    """
    script = PlutusV2Script(bytes.fromhex(validatorBlueprint["compiledCode"]))
    new_bp = copy.deepcopy(validatorBlueprint)
    new_arts = generate_artifacts(
        _build(_apply_parameters(uplc.unflatten(script), *args))
    )
    new_bp["compiledCode"] = new_arts.cbor_hex
    new_bp["hash"] = new_arts.policy_id
    # update the parameters in the blueprint (remove applied parameters)
    assert len(new_bp["parameters"]) >= len(
        args
    ), f"Applying too many parameters to contract, allowed amount: {new_bp['parameters']}, but got {len(args)}"
    for _ in args:
        new_bp["parameters"].pop(0)
    return new_bp


def _apply_parameters(script: uplc.ast.Program, *args: pycardano.Datum):
    """
    Expects a UPLC program and returns the build artifacts from applying parameters to it
    """
    # apply parameters from the command line to the contract (instantiates parameterized contract!)
    code = script.term
    # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
    for d in args:
        code = uplc.ast.Apply(
            code,
            uplc.ast.data_from_cbor(datum_to_cbor(d))
            if not isinstance(d, uplc_ast.Constant)
            else d,
        )
    code = uplc.ast.Program((1, 0, 0), code)
    return code


def load(contract_path: Union[Path, str]) -> PlutusV2Script:
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
    return PlutusV2Script(contract_cbor)


def dump(
    contract: Union[PlutusV2Script, ScriptArtifacts], target_dir: Union[str, Path]
):
    target_dir = Path(target_dir)
    target_dir.mkdir(exist_ok=True, parents=True)
    if isinstance(contract, PlutusV2Script):
        artifacts = generate_artifacts(contract)
    else:
        artifacts = contract
    with (target_dir / "script.cbor").open("w") as fp:
        fp.write(artifacts.cbor_hex)
    with (target_dir / "script.plutus").open("w") as fp:
        fp.write(artifacts.plutus_json)
    with (target_dir / "script.policy_id").open("w") as fp:
        fp.write(artifacts.policy_id)
    with (target_dir / "mainnet.addr").open("w") as fp:
        fp.write(artifacts.mainnet_addr)
    with (target_dir / "testnet.addr").open("w") as fp:
        fp.write(artifacts.testnet_addr)
    with (target_dir / "blueprint.json").open("w") as fp:
        json.dump(artifacts.blueprint, fp, indent=2)
