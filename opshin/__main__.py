import argparse
import enum
import importlib
import json
import pathlib
import sys
import typing
import ast

import pycardano
import uplc
import uplc.ast

from opshin import __version__, compiler, builder
from opshin.util import CompilerError, data_from_json


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
        "--force-three-params",
        action="store_true",
        help="Enforces that the contract is always called with three virtual parameters on-chain. Enable if the script should support spending and other purposes.",
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
        if args.input_file == "-":
            with open("__tmp_opshin.py", "w") as fp:
                fp.write(source_code)
            input_file = "__tmp_opshin.py"
        sys.path.append(str(pathlib.Path(input_file).parent.absolute()))
        sc = importlib.import_module(pathlib.Path(input_file).stem)
        sys.path.pop()
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

    source_ast = compiler.parse(source_code, filename=input_file)

    if command == Command.parse:
        print("Parsed successfully.")
        return

    try:
        code = compiler.compile(
            source_ast, filename=input_file, force_three_params=args.force_three_params
        )
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
Note that opshin errors may be overly restrictive as they aim to prevent code with unintended consequences.
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

    # apply parameters from the command line to the contract (instantiates parameterized contract!)
    code = code.term
    # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
    for d in map(data_from_json, map(json.loads, args.args)):
        code = uplc.ast.Apply(code, d)
    code = uplc.ast.Program((1, 0, 0), code)

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
            target_dir = pathlib.Path("build") / pathlib.Path(input_file).stem
        else:
            target_dir = pathlib.Path(args.output_directory)
        target_dir.mkdir(exist_ok=True, parents=True)
        artifacts = builder._build(code)
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

        print(f"Wrote script artifacts to {target_dir}/")
        return
    if command == Command.eval_uplc:
        print("Starting execution")
        print("------------------")
        assert isinstance(code, uplc.ast.Program)
        try:
            ret = uplc.dumps(uplc.eval(code))
        except Exception as e:
            print("An exception was raised")
            ret = e
        print("------------------")
        print(ret)


if __name__ == "__main__":
    main()
