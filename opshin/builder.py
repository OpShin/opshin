import copy
import dataclasses
import enum
import functools
import json
import types
import typing
from ast import Module
from typing import Optional, Any, Union
from pathlib import Path

from pycardano import PlutusV2Script, IndefiniteList, PlutusData, Datum

from . import __version__, compiler, DEFAULT_CONFIG

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
class PlutusContract:
    contract: PlutusV2Script
    datum_type: Optional[typing.Tuple[str, typing.Type[Datum]]] = None
    redeemer_type: Optional[typing.Tuple[str, typing.Type[Datum]]] = None
    parameter_types: typing.List[typing.Tuple[str, typing.Type[Datum]]] = (
        dataclasses.field(default_factory=list)
    )
    purpose: typing.Iterable[Purpose] = (Purpose.any,)
    version: Optional[str] = "1.0.0"
    title: str = "validator"
    description: Optional[str] = f"opshin {__version__} Smart Contract"
    license: Optional[str] = None

    @property
    def cbor(self) -> bytes:
        return self.contract

    @property
    def cbor_hex(self) -> str:
        return self.contract.hex()

    @property
    def script_hash(self):
        return pycardano.plutus_script_hash(self.contract)

    @property
    def policy_id(self):
        return self.script_hash.to_primitive().hex()

    @property
    def mainnet_addr(self):
        return pycardano.Address(self.script_hash, network=pycardano.Network.MAINNET)

    @property
    def testnet_addr(self):
        return pycardano.Address(self.script_hash, network=pycardano.Network.TESTNET)

    @property
    def plutus_json(self):
        return json.dumps(
            {
                "type": "PlutusScriptV2",
                "description": self.description,
                "cborHex": self.cbor_hex,
            },
            indent=2,
        )

    @property
    def blueprint(self):
        return {
            "$schema": "https://cips.cardano.org/cips/cip57/schemas/plutus-blueprint.json",
            "$id": "https://github.com/aiken-lang/aiken/blob/main/examples/hello_world/plutus.json",
            "$vocabulary": {
                "https://json-schema.org/draft/2020-12/vocab/core": True,
                "https://json-schema.org/draft/2020-12/vocab/applicator": True,
                "https://json-schema.org/draft/2020-12/vocab/validation": True,
                "https://cips.cardano.org/cips/cip57": True,
            },
            "preamble": {
                "version": self.version,
                "plutusVersion": "v2",
                "description": self.description,
                "title": self.title,
                **({"license": self.license} if self.license is not None else {}),
            },
            "validators": [
                {
                    "title": self.title,
                    **(
                        {
                            "datum": {
                                "title": self.datum_type[0],
                                "purpose": PURPOSE_MAP[Purpose.spending],
                                "schema": to_plutus_schema(self.datum_type[1]),
                            }
                        }
                        if self.datum_type is not None
                        else {}
                    ),
                    "redeemer": (
                        {
                            "title": self.redeemer_type[0],
                            "purpose": {
                                "oneOf": [PURPOSE_MAP[p] for p in self.purpose]
                            },
                            "schema": to_plutus_schema(self.redeemer_type[1]),
                        }
                        if self.redeemer_type is not None
                        else {}
                    ),
                    **(
                        {
                            "parameters": [
                                {
                                    "title": t[0],
                                    "purpose": PURPOSE_MAP[Purpose.spending],
                                    "schema": to_plutus_schema(t[1]),
                                }
                                for t in self.parameter_types
                            ]
                        }
                        if self.parameter_types
                        else {}
                    ),
                    "compiledCode": self.cbor_hex,
                    "hash": self.policy_id,
                },
            ],
        }

    def apply_parameter(self, *args: pycardano.Datum):
        """
        Returns a new OpShin Contract with the applied parameters
        """
        # update the parameters in the blueprint (remove applied parameters)
        assert len(self.parameter_types) >= len(
            args
        ), f"Applying too many parameters to contract, allowed amount: {self.parameter_types}, but got {len(args)}"
        new_parameter_types = copy.copy(self.parameter_types)
        for _ in args:
            # TODO validate that the applied parameters are of the correct type
            new_parameter_types.pop(0)
        new_contract_contract = apply_parameters(self.contract, *args)
        new_contract = PlutusContract(
            new_contract_contract,
            self.datum_type,
            self.redeemer_type,
            new_parameter_types,
            self.purpose,
            self.version,
            self.title,
            self.description,
        )
        return new_contract

    def dump(self, target_dir: Union[str, Path]):
        target_dir = Path(target_dir)
        target_dir.mkdir(exist_ok=True, parents=True)
        with (target_dir / "script.cbor").open("w") as fp:
            fp.write(self.cbor_hex)
        with (target_dir / "script.plutus").open("w") as fp:
            fp.write(self.plutus_json)
        with (target_dir / "script.policy_id").open("w") as fp:
            fp.write(self.policy_id)
        with (target_dir / "mainnet.addr").open("w") as fp:
            fp.write(self.mainnet_addr.encode())
        with (target_dir / "testnet.addr").open("w") as fp:
            fp.write(self.testnet_addr.encode())
        with (target_dir / "blueprint.json").open("w") as fp:
            json.dump(self.blueprint, fp, indent=2)


def compile(
    program: Module,
    contract_filename: Optional[str] = None,
    validator_function_name="validator",
    config=DEFAULT_CONFIG,
) -> uplc_ast.Program:
    code = compiler.compile(
        program,
        filename=contract_filename,
        validator_function_name=validator_function_name,
        config=config,
    )
    plt_code = plt_compile(code, config)
    return plt_code


@functools.lru_cache(maxsize=32)
def _static_compile(
    source_code: str,
    contract_file: str = "<unknown>",
    validator_function_name="validator",
    config=DEFAULT_CONFIG,
):
    """
    Expects a python module and returns the build artifacts from compiling it
    """

    source_ast = compiler.parse(source_code, filename=contract_file)
    code = compile(
        source_ast,
        contract_filename=contract_file,
        validator_function_name=validator_function_name,
        config=config,
    )
    return code


def _compile(
    source_code: str,
    *args: typing.Union[pycardano.Datum, uplc_ast.Constant],
    contract_file: str = "<unknown>",
    validator_function_name="validator",
    config=DEFAULT_CONFIG,
):
    """
    Expects a python module and returns the build artifacts from compiling it
    """

    code = _static_compile(
        source_code,
        contract_file=contract_file,
        validator_function_name=validator_function_name,
        config=config,
    )
    code = _apply_parameters(code, *args)
    return code


def build(
    contract_file: str,
    *args: typing.Union[pycardano.Datum, uplc_ast.Constant],
    validator_function_name="validator",
    config=DEFAULT_CONFIG,
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
        validator_function_name=validator_function_name,
        config=config,
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
            "anyOf": (
                [to_plutus_schema(t) for t in cls.__args__]
                if hasattr(cls, "__args__")
                else []
            )
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


def from_plutus_schema(schema: dict) -> typing.Type[pycardano.Datum]:
    """
    Convert from a dictionary representing a json schema according to CIP 57 Plutus Blueprint
    """
    if schema == {}:
        return pycardano.Datum
    if "anyOf" in schema:
        if len(schema["anyOf"]) == 0:
            raise ValueError("Cannot convert empty anyOf schema")
        union_t = typing.Union[from_plutus_schema(schema["anyOf"][0])]
        for s in schema["anyOf"][1:]:
            union_t = typing.Union[union_t, from_plutus_schema(s)]
        return union_t
    if "dataType" in schema:
        typ = schema["dataType"]
        if typ == "bytes":
            return bytes
        elif typ == "integer":
            return int
        elif typ == "list":
            if "items" in schema:
                return typing.List[from_plutus_schema(schema["items"])]
            else:
                return typing.List[pycardano.Datum]
        elif typ == "map":
            key_t = (
                from_plutus_schema(schema["keys"])
                if "keys" in schema
                else pycardano.Datum
            )
            value_t = (
                from_plutus_schema(schema["values"])
                if "values" in schema
                else pycardano.Datum
            )
            return typing.Dict[key_t, value_t]
        elif typ == "constructor":
            fields = {}
            for field in schema["fields"]:
                fields[field["title"]] = from_plutus_schema(field)
            fields["CONSTR_ID"] = schema["index"]
            return dataclasses.dataclass(
                type(schema["title"], (pycardano.PlutusData,), fields)
            )
    raise ValueError(f"Cannot read schema (not supported yet) {schema}")


def apply_parameters(script: PlutusV2Script, *args: pycardano.Datum):
    """
    Expects a plutus script (compiled) and returns the compiled script from applying parameters to it
    """
    return _build(_apply_parameters(uplc.unflatten(script), *args))


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
            (
                uplc.ast.data_from_cbor(datum_to_cbor(d))
                if not isinstance(d, uplc_ast.Constant)
                else d
            ),
        )
    code = uplc.ast.Program((1, 0, 0), code)
    return code


def load(contract_path: Union[Path, str]) -> PlutusContract:
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
    for contract_file in contract_candidates:
        with contract_file.open("r") as f:
            contract_content = f.read()
        # could be a plutus blueprint
        try:
            contract = json.loads(contract_content)
            if "validators" in contract:
                assert len(contract["validators"]) == 1, "Only one validator supported"
                validator = contract["validators"][0]
                contract_cbor = PlutusV2Script(bytes.fromhex(validator["compiledCode"]))
                datum_type = (
                    validator["datum"]["title"],
                    from_plutus_schema(validator["datum"]["schema"]),
                )
                redeemer_type = (
                    validator["redeemer"]["title"],
                    from_plutus_schema(validator["redeemer"]["schema"]),
                )
                parameter_types = [
                    (p["title"], from_plutus_schema(p["schema"]))
                    for p in validator["parameters"]
                ]
                if "oneOf" in validator["redeemer"]["purpose"]:
                    purpose = [
                        k
                        for k, v in PURPOSE_MAP.items()
                        if v in validator["redeemer"]["purpose"]["oneOf"]
                    ]
                else:
                    purpose = [
                        k
                        for k, v in PURPOSE_MAP.items()
                        if v == validator["redeemer"]["purpose"]
                    ]
                version = contract["preamble"].get("version")
                title = contract["preamble"].get("title")
                description = contract["preamble"].get("description")
                license = contract["preamble"].get("license")
                assert (
                    contract["preamble"].get("plutusVersion") == "v2"
                ), "Only Plutus V2 supported"
                return PlutusContract(
                    contract_cbor,
                    datum_type,
                    redeemer_type,
                    parameter_types,
                    purpose,
                    version,
                    title,
                    description,
                    license,
                )
        except (ValueError, KeyError) as e:
            pass
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
    return PlutusContract(PlutusV2Script(contract_cbor))
