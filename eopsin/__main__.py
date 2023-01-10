import json

import argparse
import enum
import pycardano
import sys
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


def plutus_data_from_json(annotation: typing.Type, x: dict):
    try:
        if annotation == int:
            return int(x["int"])
        if annotation == bytes:
            return bytes.fromhex(x["bytes"])
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
    code = code.compile()
    if command == Command.compile:
        print(code.dumps())

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
