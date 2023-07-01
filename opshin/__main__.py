import inspect

import argparse
import tempfile

import cbor2
import enum
import importlib
import json
import pathlib
import sys
import typing
import ast

import pycardano
from pycardano import PlutusData

import uplc
import uplc.ast

from . import compiler, builder, prelude, __version__, __copyright__
from .util import CompilerError, data_from_json
from .prelude import ScriptContext


class Command(enum.Enum):
    compile_pluto = "compile_pluto"
    compile = "compile"
    eval = "eval"
    parse = "parse"
    eval_uplc = "eval_uplc"
    build = "build"
    lint = "lint"


class Purpose(enum.Enum):
    spending = "spending"
    minting = "minting"
    rewarding = "rewarding"
    certifying = "certifying"
    any = "any"
    lib = "lib"


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
            if annotation == pycardano.Datum:
                if "int" in x:
                    return int(x["int"])
                if "bytes" in x:
                    return bytes.fromhex(x["bytes"])
                if "constructor" in x:
                    return pycardano.RawCBOR(
                        uplc.ast.plutus_cbor_dumps(uplc.ast.data_from_json_dict(x))
                    )
        if issubclass(annotation, pycardano.PlutusData):
            return annotation.from_dict(x)
    except (KeyError, ValueError):
        raise ValueError(
            f"Annotation {annotation} does not match provided plutus datum {json.dumps(x)}"
        )


def plutus_data_from_cbor(annotation: typing.Type, x: bytes):
    try:
        if annotation in (int, bytes):
            return cbor2.loads(x)
        if annotation is None:
            return None
        if isinstance(annotation, typing._GenericAlias):
            # Annotation is a List or Dict
            if annotation._name == "List":
                annotation_ann = annotation.__dict__["__args__"][0]
                return [
                    plutus_data_from_cbor(annotation_ann, cbor2.dumps(k))
                    for k in cbor2.loads(x)
                ]
            if annotation._name == "Dict":
                annotation_key, annotation_val = annotation.__dict__["__args__"]
                return {
                    plutus_data_from_cbor(
                        annotation_key, cbor2.dumps(k)
                    ): plutus_data_from_cbor(annotation_val, v)
                    for k, v in cbor2.loads(x).items()
                }
        if issubclass(annotation, pycardano.PlutusData):
            return annotation.from_cbor(x)
    except (KeyError, ValueError):
        raise ValueError(
            f"Annotation {annotation} does not match provided plutus datum {x.hex()}"
        )


def check_params(
    command: Command,
    purpose: Purpose,
    validator_args,
    validator_params,
    force_three_params=False,
):
    if purpose == Purpose.any:
        # The any purpose does not do any checks. Use only if you know what you are doing
        return
    ret_type = validator_args[-1]
    # expect the validator to return None
    assert (
        ret_type is None or ret_type == prelude.Anything
    ), f"Expected contract to return None, but returns {ret_type}"

    num_onchain_params = 3 if purpose == Purpose.spending or force_three_params else 2
    onchain_params = validator_args[-1 - num_onchain_params : -1]
    param_types = validator_args[: -1 - num_onchain_params]
    required_onchain_parameters = 3 if purpose == Purpose.spending else 2
    assert (
        len(onchain_params) == required_onchain_parameters
    ), f"""\
{purpose.value.capitalize()} validator must expect {required_onchain_parameters} parameters at evaluation (on-chain), but was specified to have {len(onchain_params)}.
Make sure the validator expects parameters {'datum, ' if purpose == Purpose.spending else ''}redeemer and script context."""

    if command in (Command.eval, Command.eval_uplc):
        assert len(validator_params) == len(param_types) + len(
            onchain_params
        ), f"{purpose.value.capitalize()} validator expects {len(param_types) + len(onchain_params)} parameters for evaluation, but only got {len(validator_params)}."
    else:
        assert len(validator_params) == len(
            param_types
        ), f"{purpose.value.capitalize()} validator expects {len(onchain_params)} parameters at evaluation (on-chain) and {len(param_types)} parameters at compilation time, but got {len(validator_params)} during compilation."
    assert (
        onchain_params[-1] == ScriptContext
    ), f"Last parameter of the validator is always ScriptContext, but is {onchain_params[-1].__name__} here."


def perform_command(args):
    command = Command(args.command)
    purpose = Purpose(args.purpose)
    input_file = args.input_file if args.input_file != "-" else sys.stdin
    force_three_params = args.force_three_params
    constant_folding = args.constant_folding
    # read and import the contract
    with open(input_file, "r") as f:
        source_code = f.read()
    with tempfile.TemporaryDirectory(prefix="build") as tmpdir:
        tmp_input_file = pathlib.Path(tmpdir).joinpath("__tmp_opshin.py")
        with tmp_input_file.open("w") as fp:
            fp.write(source_code)
        sys.path.append(str(pathlib.Path(tmp_input_file).parent.absolute()))
        sc = importlib.import_module(pathlib.Path(tmp_input_file).stem)
        sys.path.pop()
    # load the passed parameters if not a lib
    if purpose == Purpose.lib:
        assert not args.args, "Can not pass arguments to a library"
        parsed_params = []
    else:
        try:
            argspec = inspect.getfullargspec(sc.validator)
        except AttributeError:
            raise AssertionError(
                f"Contract has no function called 'validator'. Make sure the compiled contract contains one function called 'validator' or {command.value} using `opshin {command.value} lib {str(input_file)}`."
            )
        annotations = [
            argspec.annotations.get(x, prelude.Anything) for x in argspec.args
        ]
        annotations.append(sc.validator.__annotations__.get("return", prelude.Anything))
        parsed_params = []
        for i, (c, a) in enumerate(zip(annotations, args.args)):
            if a[0] == "{":
                try:
                    param_json = json.loads(a)
                except Exception as e:
                    raise ValueError(
                        f'Invalid parameter for contract passed at position {i}, expected json value, got "{a}". Did you correctly encode the value as json and wrap it in quotes?'
                    ) from e
                try:
                    param = plutus_data_from_json(c, param_json)
                except Exception as e:
                    raise ValueError(
                        f"Invalid parameter for contract passed at position {i}, expected type {c.__name__}."
                    ) from e
            else:
                try:
                    param_bytes = bytes.fromhex(a)
                except Exception as e:
                    raise ValueError(
                        "Expected hexadecimal CBOR representation of plutus datum but could not transform hex string to bytes."
                    ) from e
                try:
                    param = plutus_data_from_cbor(c, param_bytes)
                except Exception as e:
                    raise ValueError(
                        f"Invalid parameter for contract passed at position {i}, expected type {c.__name__}."
                    ) from e
            parsed_params.append(param)
        check_params(
            command,
            purpose,
            annotations,
            parsed_params,
            force_three_params,
        )

    if command == Command.eval:
        assert purpose != Purpose.lib, "Can not evaluate a library"
        print("Starting execution")
        print("------------------")
        try:
            ret = sc.validator(*parsed_params)
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
            source_ast,
            filename=input_file,
            force_three_params=force_three_params,
            validator_function_name="validator" if purpose != Purpose.lib else None,
            constant_folding=constant_folding,
            # do not remove dead code when compiling a library - none of the code will be used
            remove_dead_code=purpose != Purpose.lib,
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

        overwrite_syntaxerror = (
            len("SyntaxError: ") * "\b" if command != Command.lint else ""
        )
        err = SyntaxError(
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
        )
        err.orig_err = c.orig_err
        raise err from None

    if command == Command.compile_pluto:
        print(code.dumps())
        return
    code = code.compile()

    # apply parameters from the command line to the contract (instantiates parameterized contract!)
    code = code.term
    # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
    for d in map(
        data_from_json,
        map(json.loads, (PlutusData.to_json(p) for p in parsed_params)),
    ):
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
        artifacts = builder.generate_artifacts(builder._build(code))
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


def parse_args():
    a = argparse.ArgumentParser(
        description="An evaluator and compiler from python into UPLC. Translate imperative programs into functional quasi-assembly."
    )
    a.add_argument(
        "command",
        type=str,
        choices=Command.__members__.keys(),
        help="The command to execute on the input file.",
        default="eval",
        nargs="?",
    )
    a.add_argument(
        "purpose",
        type=str,
        choices=Purpose.__members__.keys(),
        help="The intended script purpose. Determines the number of on-chain parameters "
        "(spending = 3, minting, rewarding, certifying = 2, any = no checks). "
        "This allows the compiler to check whether the correct amount of parameters was passed during compilation.",
        default="any",
        nargs="?",
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
        "--ftp",
        action="store_true",
        help="Enforces that the contract is always called with three virtual parameters on-chain. Enable if the script should support spending and other purposes.",
    )
    a.add_argument(
        "--constant-folding",
        "--cf",
        action="store_true",
        help="Enables experimental constant folding, including propagation and code execution.",
    )
    a.add_argument(
        "args",
        nargs="*",
        default=[],
        help="Input parameters for the validator (parameterizes the contract for compile/build). Either json or CBOR notation.",
    )
    a.add_argument(
        "--output-format-json",
        action="store_true",
        help="Changes the output of the Linter to a json format.",
    )
    a.add_argument(
        "--version",
        action="version",
        version=f"opshin {__version__} {__copyright__}",
    )
    return a.parse_args()


def main():
    args = parse_args()
    if Command(args.command) != Command.lint:
        perform_command(args)
    else:
        try:
            perform_command(args)
        except Exception as e:
            error_class_name = e.__class__.__name__
            message = str(e)
            if isinstance(e, SyntaxError):
                start_line = e.lineno
                pos_in_line = e.offset
                if hasattr(e, "orig_err"):
                    error_class_name = e.orig_err.__class__.__name__
                    message = str(e.orig_err)
            else:
                start_line = 1
                pos_in_line = 1
            if args.output_format_json:
                print(
                    convert_linter_to_json(
                        line=start_line,
                        column=pos_in_line,
                        error_class=error_class_name,
                        message=message,
                    )
                )
            else:
                print(
                    f"{args.input_file}:{start_line}:{pos_in_line}: {error_class_name}: {message}"
                )


def convert_linter_to_json(
    line: int,
    column: int,
    error_class: str,
    message: str,
):
    # output in lists
    return json.dumps(
        [
            {
                "line": line,
                "column": column,
                "error_class": error_class,
                "message": message,
            }
        ]
    )


if __name__ == "__main__":
    main()
