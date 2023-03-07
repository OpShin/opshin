import ast
from enum import Enum, auto

from .typed_ast import *

import pluthon as plt
import uplc.ast as uplc


def PowImpl(x: plt.AST, y: plt.AST):
    return plt.Apply(
        plt.RecFun(
            plt.Lambda(
                ["f", "x", "y"],
                plt.Ite(
                    plt.LessThanEqualsInteger(plt.Var("y"), plt.Integer(0)),
                    plt.Integer(1),
                    plt.MultiplyInteger(
                        plt.Var("x"),
                        plt.Apply(
                            plt.Var("f"),
                            plt.Var("f"),
                            plt.Var("x"),
                            plt.SubtractInteger(plt.Var("y"), plt.Integer(1)),
                        ),
                    ),
                ),
            ),
        ),
        x,
        y,
    )


class PythonBuiltIn(Enum):
    all = plt.Lambda(
        ["xs", "_"],
        plt.FoldList(
            plt.Var("xs"),
            plt.Lambda(["x", "a"], plt.And(plt.Var("x"), plt.Var("a"))),
            plt.Bool(True),
        ),
    )
    any = plt.Lambda(
        ["xs", "_"],
        plt.FoldList(
            plt.Var("xs"),
            plt.Lambda(["x", "a"], plt.Or(plt.Var("x"), plt.Var("a"))),
            plt.Bool(False),
        ),
    )
    abs = plt.Lambda(
        ["x", "_"],
        plt.Ite(
            plt.LessThanInteger(plt.Var("x"), plt.Integer(0)),
            plt.Negate(plt.Var("x")),
            plt.Var("x"),
        ),
    )
    # maps an integer to a unicode code point and decodes it
    # reference: https://en.wikipedia.org/wiki/UTF-8#Encoding
    chr = plt.Lambda(
        ["x", "_"],
        plt.DecodeUtf8(
            plt.Ite(
                plt.LessThanInteger(plt.Var("x"), plt.Integer(0x0)),
                plt.TraceError("ValueError: chr() arg not in range(0x110000)"),
                plt.Ite(
                    plt.LessThanInteger(plt.Var("x"), plt.Integer(0x80)),
                    # encoding of 0x0 - 0x80
                    plt.ConsByteString(plt.Var("x"), plt.ByteString(b"")),
                    plt.Ite(
                        plt.LessThanInteger(plt.Var("x"), plt.Integer(0x800)),
                        # encoding of 0x80 - 0x800
                        plt.ConsByteString(
                            # we do bit manipulation using integer arithmetic here - nice
                            plt.AddInteger(
                                plt.Integer(0b110 << 5),
                                plt.DivideInteger(plt.Var("x"), plt.Integer(1 << 6)),
                            ),
                            plt.ConsByteString(
                                plt.AddInteger(
                                    plt.Integer(0b10 << 6),
                                    plt.ModInteger(plt.Var("x"), plt.Integer(1 << 6)),
                                ),
                                plt.ByteString(b""),
                            ),
                        ),
                        plt.Ite(
                            plt.LessThanInteger(plt.Var("x"), plt.Integer(0x10000)),
                            # encoding of 0x800 - 0x10000
                            plt.ConsByteString(
                                plt.AddInteger(
                                    plt.Integer(0b1110 << 4),
                                    plt.DivideInteger(
                                        plt.Var("x"), plt.Integer(1 << 12)
                                    ),
                                ),
                                plt.ConsByteString(
                                    plt.AddInteger(
                                        plt.Integer(0b10 << 6),
                                        plt.DivideInteger(
                                            plt.ModInteger(
                                                plt.Var("x"), plt.Integer(1 << 12)
                                            ),
                                            plt.Integer(1 << 6),
                                        ),
                                    ),
                                    plt.ConsByteString(
                                        plt.AddInteger(
                                            plt.Integer(0b10 << 6),
                                            plt.ModInteger(
                                                plt.Var("x"), plt.Integer(1 << 6)
                                            ),
                                        ),
                                        plt.ByteString(b""),
                                    ),
                                ),
                            ),
                            plt.Ite(
                                plt.LessThanInteger(
                                    plt.Var("x"), plt.Integer(0x110000)
                                ),
                                # encoding of 0x10000 - 0x10FFF
                                plt.ConsByteString(
                                    plt.AddInteger(
                                        plt.Integer(0b11110 << 3),
                                        plt.DivideInteger(
                                            plt.Var("x"), plt.Integer(1 << 18)
                                        ),
                                    ),
                                    plt.ConsByteString(
                                        plt.AddInteger(
                                            plt.Integer(0b10 << 6),
                                            plt.DivideInteger(
                                                plt.ModInteger(
                                                    plt.Var("x"), plt.Integer(1 << 18)
                                                ),
                                                plt.Integer(1 << 12),
                                            ),
                                        ),
                                        plt.ConsByteString(
                                            plt.AddInteger(
                                                plt.Integer(0b10 << 6),
                                                plt.DivideInteger(
                                                    plt.ModInteger(
                                                        plt.Var("x"),
                                                        plt.Integer(1 << 12),
                                                    ),
                                                    plt.Integer(1 << 6),
                                                ),
                                            ),
                                            plt.ConsByteString(
                                                plt.AddInteger(
                                                    plt.Integer(0b10 << 6),
                                                    plt.ModInteger(
                                                        plt.Var("x"),
                                                        plt.Integer(1 << 6),
                                                    ),
                                                ),
                                                plt.ByteString(b""),
                                            ),
                                        ),
                                    ),
                                ),
                                plt.TraceError(
                                    "ValueError: chr() arg not in range(0x110000)"
                                ),
                            ),
                        ),
                    ),
                ),
            )
        ),
    )
    breakpoint = plt.Lambda(["_"], plt.NoneData())
    hex = plt.Lambda(
        ["x", "_"],
        plt.DecodeUtf8(
            plt.Let(
                [
                    (
                        "hexlist",
                        plt.RecFun(
                            plt.Lambda(
                                ["f", "i"],
                                plt.Ite(
                                    plt.LessThanEqualsInteger(
                                        plt.Var("i"), plt.Integer(0)
                                    ),
                                    plt.EmptyIntegerList(),
                                    plt.MkCons(
                                        plt.Let(
                                            [
                                                (
                                                    "mod",
                                                    plt.ModInteger(
                                                        plt.Var("i"), plt.Integer(16)
                                                    ),
                                                ),
                                            ],
                                            plt.AddInteger(
                                                plt.Var("mod"),
                                                plt.IfThenElse(
                                                    plt.LessThanInteger(
                                                        plt.Var("mod"), plt.Integer(10)
                                                    ),
                                                    plt.Integer(ord("0")),
                                                    plt.Integer(ord("a") - 10),
                                                ),
                                            ),
                                        ),
                                        plt.Apply(
                                            plt.Var("f"),
                                            plt.Var("f"),
                                            plt.DivideInteger(
                                                plt.Var("i"), plt.Integer(16)
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "mkstr",
                        plt.Lambda(
                            ["i"],
                            plt.FoldList(
                                plt.Apply(plt.Var("hexlist"), plt.Var("i")),
                                plt.Lambda(
                                    ["b", "i"],
                                    plt.ConsByteString(plt.Var("i"), plt.Var("b")),
                                ),
                                plt.ByteString(b""),
                            ),
                        ),
                    ),
                ],
                plt.Ite(
                    plt.EqualsInteger(plt.Var("x"), plt.Integer(0)),
                    plt.ByteString(b"0x0"),
                    plt.Ite(
                        plt.LessThanInteger(plt.Var("x"), plt.Integer(0)),
                        plt.ConsByteString(
                            plt.Integer(ord("-")),
                            plt.AppendByteString(
                                plt.ByteString(b"0x"),
                                plt.Apply(plt.Var("mkstr"), plt.Negate(plt.Var("x"))),
                            ),
                        ),
                        plt.AppendByteString(
                            plt.ByteString(b"0x"),
                            plt.Apply(plt.Var("mkstr"), plt.Var("x")),
                        ),
                    ),
                ),
            )
        ),
    )
    len = auto()
    max = plt.Lambda(
        ["xs", "_"],
        plt.FoldList(
            plt.TailList(plt.Var("xs")),
            plt.Lambda(
                ["x", "a"],
                plt.IfThenElse(
                    plt.LessThanInteger(plt.Var("a"), plt.Var("x")),
                    plt.Var("x"),
                    plt.Var("a"),
                ),
            ),
            plt.HeadList(plt.Var("xs")),
        ),
    )
    min = plt.Lambda(
        ["xs", "_"],
        plt.FoldList(
            plt.TailList(plt.Var("xs")),
            plt.Lambda(
                ["x", "a"],
                plt.IfThenElse(
                    plt.LessThanInteger(plt.Var("a"), plt.Var("x")),
                    plt.Var("a"),
                    plt.Var("x"),
                ),
            ),
            plt.HeadList(plt.Var("xs")),
        ),
    )
    print = plt.Lambda(
        ["x", "_"],
        plt.Trace(plt.Var("x"), plt.NoneData()),
    )
    # NOTE: only correctly defined for positive y
    pow = plt.Lambda(["x", "y", "_"], PowImpl(plt.Var("x"), plt.Var("y")))
    oct = plt.Lambda(
        ["x", "_"],
        plt.DecodeUtf8(
            plt.Let(
                [
                    (
                        "octlist",
                        plt.RecFun(
                            plt.Lambda(
                                ["f", "i"],
                                plt.Ite(
                                    plt.LessThanEqualsInteger(
                                        plt.Var("i"), plt.Integer(0)
                                    ),
                                    plt.EmptyIntegerList(),
                                    plt.MkCons(
                                        plt.AddInteger(
                                            plt.ModInteger(
                                                plt.Var("i"), plt.Integer(8)
                                            ),
                                            plt.Integer(ord("0")),
                                        ),
                                        plt.Apply(
                                            plt.Var("f"),
                                            plt.Var("f"),
                                            plt.DivideInteger(
                                                plt.Var("i"), plt.Integer(8)
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "mkoct",
                        plt.Lambda(
                            ["i"],
                            plt.FoldList(
                                plt.Apply(plt.Var("octlist"), plt.Var("i")),
                                plt.Lambda(
                                    ["b", "i"],
                                    plt.ConsByteString(plt.Var("i"), plt.Var("b")),
                                ),
                                plt.ByteString(b""),
                            ),
                        ),
                    ),
                ],
                plt.Ite(
                    plt.EqualsInteger(plt.Var("x"), plt.Integer(0)),
                    plt.ByteString(b"0o0"),
                    plt.Ite(
                        plt.LessThanInteger(plt.Var("x"), plt.Integer(0)),
                        plt.ConsByteString(
                            plt.Integer(ord("-")),
                            plt.AppendByteString(
                                plt.ByteString(b"0o"),
                                plt.Apply(plt.Var("mkoct"), plt.Negate(plt.Var("x"))),
                            ),
                        ),
                        plt.AppendByteString(
                            plt.ByteString(b"0o"),
                            plt.Apply(plt.Var("mkoct"), plt.Var("x")),
                        ),
                    ),
                ),
            )
        ),
    )
    range = plt.Lambda(
        ["limit", "_"],
        plt.Range(plt.Var("limit")),
    )
    reversed = auto()
    sum = plt.Lambda(
        ["xs", "_"],
        plt.FoldList(
            plt.Var("xs"), plt.BuiltIn(uplc.BuiltInFun.AddInteger), plt.Integer(0)
        ),
    )


class LenImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 1
        ), f"'len' takes only one argument, but {len(args)} were given"
        assert isinstance(
            args[0], InstanceType
        ), "Can only determine length of instances"
        return FunctionType(args, IntegerInstanceType)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(arg, InstanceType), "Can only determine length of instances"
        if arg == ByteStringInstanceType:
            return plt.Lambda(["x", "_"], plt.LengthOfByteString(plt.Var("x")))
        elif isinstance(arg.typ, ListType):
            # simple list length function
            return plt.Lambda(
                ["x", "_"],
                plt.FoldList(
                    plt.Var("x"),
                    plt.Lambda(
                        ["a", "_"], plt.AddInteger(plt.Var("a"), plt.Integer(1))
                    ),
                    plt.Integer(0),
                ),
            )
        raise NotImplementedError(f"'len' is not implemented for type {arg}")


class ReversedImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 1
        ), f"'reversed' takes only one argument, but {len(args)} were given"
        typ = args[0]
        assert isinstance(typ, InstanceType), "Can only reverse instances"
        assert isinstance(typ.typ, ListType), "Can only reverse instances of lists"
        # returns list of same type
        return FunctionType(args, typ)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(arg, InstanceType), "Can only reverse instances"
        if isinstance(arg.typ, ListType):
            empty_l = empty_list(arg.typ.typ)
            return plt.Lambda(
                ["xs", "_"],
                plt.FoldList(
                    plt.Var("xs"),
                    plt.Lambda(["a", "x"], plt.MkCons(plt.Var("x"), plt.Var("a"))),
                    empty_l,
                ),
            )
        raise NotImplementedError(f"'reversed' is not implemented for type {arg}")


PythonBuiltInTypes = {
    PythonBuiltIn.all: InstanceType(
        FunctionType(
            [InstanceType(ListType(BoolInstanceType))],
            BoolInstanceType,
        )
    ),
    PythonBuiltIn.any: InstanceType(
        FunctionType(
            [InstanceType(ListType(BoolInstanceType))],
            BoolInstanceType,
        )
    ),
    PythonBuiltIn.abs: InstanceType(
        FunctionType(
            [IntegerInstanceType],
            IntegerInstanceType,
        )
    ),
    PythonBuiltIn.chr: InstanceType(
        FunctionType(
            [IntegerInstanceType],
            StringInstanceType,
        )
    ),
    PythonBuiltIn.breakpoint: InstanceType(FunctionType([], NoneInstanceType)),
    PythonBuiltIn.len: InstanceType(PolymorphicFunctionType(LenImpl())),
    PythonBuiltIn.hex: InstanceType(
        FunctionType(
            [IntegerInstanceType],
            StringInstanceType,
        )
    ),
    PythonBuiltIn.max: InstanceType(
        FunctionType(
            [InstanceType(ListType(IntegerInstanceType))],
            IntegerInstanceType,
        )
    ),
    PythonBuiltIn.min: InstanceType(
        FunctionType(
            [InstanceType(ListType(IntegerInstanceType))],
            IntegerInstanceType,
        )
    ),
    PythonBuiltIn.print: InstanceType(
        FunctionType([StringInstanceType], NoneInstanceType)
    ),
    PythonBuiltIn.pow: InstanceType(
        FunctionType(
            [IntegerInstanceType, IntegerInstanceType],
            IntegerInstanceType,
        )
    ),
    PythonBuiltIn.oct: InstanceType(
        FunctionType(
            [IntegerInstanceType],
            StringInstanceType,
        )
    ),
    PythonBuiltIn.range: InstanceType(
        FunctionType(
            [IntegerInstanceType],
            InstanceType(ListType(IntegerInstanceType)),
        )
    ),
    PythonBuiltIn.reversed: InstanceType(PolymorphicFunctionType(ReversedImpl())),
    PythonBuiltIn.sum: InstanceType(
        FunctionType(
            [InstanceType(ListType(IntegerInstanceType))],
            IntegerInstanceType,
        )
    ),
}


class CompilerError(Exception):
    def __init__(self, orig_err: Exception, node: ast.AST, compilation_step: str):
        self.orig_err = orig_err
        self.node = node
        self.compilation_step = compilation_step


class CompilingNodeTransformer(TypedNodeTransformer):
    step = "Node transformation"

    def visit(self, node):
        try:
            return super().visit(node)
        except Exception as e:
            if isinstance(e, CompilerError):
                raise e
            raise CompilerError(e, node, self.step)


class CompilingNodeVisitor(TypedNodeVisitor):
    step = "Node visiting"

    def visit(self, node):
        try:
            return super().visit(node)
        except Exception as e:
            if isinstance(e, CompilerError):
                raise e
            raise CompilerError(e, node, self.step)


def data_from_json(j: typing.Dict[str, typing.Any]) -> uplc.PlutusData:
    if "bytes" in j:
        return uplc.PlutusByteString(bytes.fromhex(j["bytes"]))
    if "int" in j:
        return uplc.PlutusInteger(int(j["int"]))
    if "list" in j:
        return uplc.PlutusList(list(map(data_from_json, j["list"])))
    if "map" in j:
        return uplc.PlutusMap({d["k"]: d["v"] for d in j["map"]})
    if "constructor" in j and "fields" in j:
        return uplc.PlutusConstr(
            j["constructor"], list(map(data_from_json, j["fields"]))
        )
    raise NotImplementedError(f"Unknown datum representation {j}")
