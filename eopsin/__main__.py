import argparse
import enum
import sys
import importlib

from eopsin import compiler


class Command(enum.Enum):
    compile = "compile"
    eval = "eval"
    parse = "parse"


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
        source_code = "".join(l for l in f)

    if command == Command.eval:
        with open("__tmp_pyscc.py", "w") as fp:
            fp.write(source_code)
        sc = importlib.import_module("__tmp_pyscc")
        print("Starting execution")
        print("------------------")
        try:
            ret = sc.main(*args.args)
        except Exception as e:
            print(f"Exception of type {type(e).__name__} caused")
            ret = e
        print("------------------")
        print(ret)

    ast = compiler.parse(source_code)

    if command == Command.parse:
        print("Parsed successfully.")
        return

    if command == Command.compile:
        code = compiler.compile(ast)
        print(code.dumps())


if __name__ == "__main__":
    main()
