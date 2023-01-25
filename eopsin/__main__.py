import argparse
import enum
import importlib
import json
import pathlib
import sys
import typing
import ast

import cbor2
import pyaiken
import pycardano
import uplc
import uplc.ast

from eopsin import __version__, compiler
from eopsin.util import CompilerError


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

    source_ast = compiler.parse(source_code)

    if command == Command.parse:
        print("Parsed successfully.")
        return

    try:
        code = compiler.compile(source_ast)
    except CompilerError as c:
        # Generate nice error message from compiler error
        if not isinstance(c.node, ast.Module):
            source_seg = ast.get_source_segment(source_code, c.node)
            start_line = c.node.lineno - 1
            end_line = start_line + len(source_seg.splitlines())
            source_lines = "\n".join(source_code.splitlines()[start_line:end_line])
            pos_in_line = source_lines.find(source_seg)
        else:
            start_line = 0
            pos_in_line = 0
            source_lines = source_code.splitlines()[0]
        overwrite_syntaxerror = len("SyntaxError: ") * "\b"
        raise SyntaxError(
            f"""\
{overwrite_syntaxerror}{c.orig_err.__class__.__name__}: {c.orig_err}
Note that eopsin errors may be overly restrictive as they aim to prevent code with unintended consequences.
""",
            (
                args.input_file,
                start_line + 1,
                pos_in_line,
                source_lines,
            )
            # we remove chaining so that users to not see the internal trace back,
        ) from None

    if command == Command.compile_pluto:
        print(code.dumps())
        return
    code = code.compile()
    if command == Command.compile:
        print(code.dumps())
        return

    if command == Command.build:
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
        # create cbor file for use with pycardano/lucid
        with (target_dir / "script.cbor").open("w") as fp:
            fp.write(cbor_hex)
        cbor = bytes.fromhex(cbor_hex)
        # double wrap
        cbor_wrapped = cbor2.dumps(cbor)
        cbor_wrapped_hex = cbor_wrapped.hex()
        # create plutus file
        d = {
            "type": "PlutusScriptV2",
            "description": f"Eopsin {__version__} Smart Contract",
            "cborHex": cbor_wrapped_hex,
        }
        with (target_dir / "script.plutus").open("w") as fp:
            json.dump(d, fp)
        script_hash = pycardano.plutus_script_hash(pycardano.PlutusV2Script(cbor))
        # generate policy ids
        with (target_dir / "script.policy_id").open("w") as fp:
            fp.write(script_hash.to_primitive().hex())
        addr_mainnet = pycardano.Address(
            script_hash, network=pycardano.Network.MAINNET
        ).encode()
        # generate addresses
        with (target_dir / "mainnet.addr").open("w") as fp:
            fp.write(addr_mainnet)
        addr_testnet = pycardano.Address(
            script_hash, network=pycardano.Network.TESTNET
        ).encode()
        with (target_dir / "testnet.addr").open("w") as fp:
            fp.write(addr_testnet)

        print(f"Wrote script artifacts to {target_dir}/")
        return
    if command == Command.eval_uplc:
        print("Starting execution")
        print("------------------")
        assert isinstance(code, uplc.ast.Program)
        try:
            f = code.term
            # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
            for d in map(uplc.ast.data_from_json, map(json.loads, args.args)):
                f = uplc.ast.Apply(f, d)
            ret = uplc.dumps(uplc.eval(f))
        except Exception as e:
            print("An exception was raised")
            ret = e
        print("------------------")
        print(ret)


if __name__ == "__main__":
    main()
