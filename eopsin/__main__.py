import cbor2
import json

import argparse
import enum
import pycardano
import sys
import pathlib
import importlib
import typing

import uplc
from eopsin import compiler
from uplc import data_from_json


class Command(enum.Enum):
    compile_pluto = "compile_pluto"
    compile = "compile"
    eval = "eval"
    parse = "parse"
    eval_uplc = "eval_uplc"
    build = "build"


def plutus_data_from_json(annotation: typing.Type, x: dict):
    try:
        if annotation == int:
            return int(x["int"])
        if annotation == bytes:
            return bytes.fromhex(x["bytes"])
        if annotation is None:
            return None
        if isinstance(annotation, typing._GenericAlias):
            # Annotation is a List or Dict
            if annotation._name == "List":
                annotation_ann = annotation.__dict__["__args__"][0]
                return [plutus_data_from_json(annotation_ann, k) for k in x["list"]]
            if annotation._name == "Dict":
                annotation_key, annotation_val = annotation.__dict__["__args__"]
                return {
                    plutus_data_from_json(
                        annotation_key, d["k"]
                    ): plutus_data_from_json(annotation_val, d["v"])
                    for d in x["map"]
                }
        if issubclass(annotation, pycardano.PlutusData):
            return annotation.from_dict(x)
    except (KeyError, ValueError):
        raise ValueError(
            f"Annotation {annotation} does not match provided plutus datum {json.dumps(x)}"
        )


def main():
    a = argparse.ArgumentParser(
        description="An evaluator and compiler from python into UPLC. Translate imperative programs into functional quasi-assembly."
    )
    a.add_argument(
        "command",
        type=str,
        choices=Command.__members__.keys(),
        help="The command to execute on the input file.",
    )
    a.add_argument(
        "input_file", type=str, help="The input program to parse. Set to - for stdin."
    )
    a.add_argument(
        "-o",
        "--output-directory",
        default="",
        type=str,
        help="The output directory for artefacts of the build command. Defaults to the filename of the compiled contract. of the compiled contract.",
    )
    a.add_argument(
        "args",
        nargs="*",
        default=[],
        help="Input parameters for the function, in case the command is eval.",
    )
    args = a.parse_args()
    command = Command(args.command)
    input_file = args.input_file if args.input_file != "-" else sys.stdin
    with open(input_file, "r") as f:
        source_code = f.read()

    if command == Command.eval:
        with open("__tmp_eopsin.py", "w") as fp:
            fp.write(source_code)
        sc = importlib.import_module("__tmp_eopsin")
        print("Starting execution")
        print("------------------")
        try:
            parsed_args = [
                plutus_data_from_json(c, json.loads(a))
                for c, a, in zip(sc.validator.__annotations__.values(), args.args)
            ]
            ret = sc.validator(*parsed_args)
        except Exception as e:
            print(f"Exception of type {type(e).__name__} caused")
            ret = e
        print("------------------")
        print(ret)

    ast = compiler.parse(source_code)

    if command == Command.parse:
        print("Parsed successfully.")
        return

    code = compiler.compile(ast)
    if command == Command.compile_pluto:
        print(code.dumps())
        return
    code = code.compile()
    if command == Command.compile:
        print(code.dumps())
        return

    if command == Command.build:
        try:
            import pyaiken
        except ImportError:
            print(
                "Package pyaiken is not installed. The build command is not available. Install via `pip install pyaiken`."
            )
            exit(-1)
        if args.output_directory == "":
            if args.input_file == "-":
                print(
                    "Please supply an output directory if no input file is specified."
                )
                exit(-1)
            target_dir = pathlib.Path(pathlib.Path(input_file).stem)
        else:
            target_dir = pathlib.Path(args.output_directory)
        target_dir.mkdir(exist_ok=True)
        uplc_dump = code.dumps()
        cbor_hex = pyaiken.uplc.flat(uplc_dump)
        with (target_dir / "script.cbor").open("w") as fp:
            fp.write(cbor_hex)
        cbor = bytes.fromhex(cbor_hex)
        # double wrap
        cbor_wrapped = cbor2.dumps(cbor)
        cbor_wrapped_hex = cbor_wrapped.hex()
        d = {
            "type": "PlutusScriptV2",
            "description": "Eopsin Smart Contract",
            "cborHex": cbor_wrapped_hex,
        }
        with (target_dir / "script.plutus").open("w") as fp:
            json.dump(d, fp)
        addr_mainnet = pyaiken.script_address.build_mainnet(cbor_hex)
        with (target_dir / "mainnet.addr").open("w") as fp:
            fp.write(addr_mainnet)
        addr_testnet = pyaiken.script_address.build_testnet(cbor_hex)
        with (target_dir / "testnet.addr").open("w") as fp:
            fp.write(addr_testnet)
        print(f"Wrote script artifacts to {target_dir}/")
        return

    if command == Command.eval_uplc:
        print("Starting execution")
        print("------------------")
        assert isinstance(code, uplc.Program)
        try:
            f = code.term
            # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
            for d in map(data_from_json, map(json.loads, args.args)):
                f = uplc.Apply(f, d)
            ret = uplc.Machine(f).eval().dumps()
        except Exception as e:
            print("An exception was raised")
            ret = e
        print("------------------")
        print(ret)


if __name__ == "__main__":
    main()
