from enum import Enum

from .typed_ast import *


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
            return OLambda(["x"], plt.LengthOfByteString(OVar("x")))
        elif isinstance(arg.typ, ListType) or isinstance(arg.typ, DictType):
            # simple list length function
            return OLambda(
                ["x"],
                plt.FoldList(
                    OVar("x"),
                    OLambda(["a", "_"], plt.AddInteger(OVar("a"), plt.Integer(1))),
                    plt.Integer(0),
                ),
            )
        elif isinstance(arg.typ, TupleType):
            return OLambda(
                ["x"],
                plt.Integer(len(arg.typ.typs)),
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
            return OLambda(
                ["xs"],
                plt.FoldList(
                    OVar("xs"),
                    OLambda(["a", "x"], plt.MkCons(OVar("x"), OVar("a"))),
                    empty_l,
                ),
            )
        raise NotImplementedError(f"'reversed' is not implemented for type {arg}")


class PrintImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert all(
            isinstance(typ, InstanceType) for typ in args
        ), "Can only print instances"
        return FunctionType(args, NoneInstanceType)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        if not args:
            return SafeOLambda([], plt.Trace(plt.Text("\n"), plt.NoneData()))
        assert all(
            isinstance(arg, InstanceType) for arg in args
        ), "Can only stringify instances"
        stringify_ops = [
            plt.Apply(arg.typ.stringify(), OVar(f"x{i}")) for i, arg in enumerate(args)
        ]
        stringify_ops_joined = sum(((x, plt.Text(" ")) for x in stringify_ops), ())[:-1]
        print = SafeOLambda(
            [f"x{i}" for i in range(len(args))],
            plt.Trace(plt.ConcatString(*stringify_ops_joined), plt.NoneData()),
        )
        return print


class PythonBuiltIn(Enum):
    all = OLambda(
        ["xs"],
        plt.FoldList(
            OVar("xs"),
            OLambda(["x", "a"], plt.And(OVar("x"), OVar("a"))),
            plt.Bool(True),
        ),
    )
    any = OLambda(
        ["xs"],
        plt.FoldList(
            OVar("xs"),
            OLambda(["x", "a"], plt.Or(OVar("x"), OVar("a"))),
            plt.Bool(False),
        ),
    )
    abs = OLambda(
        ["x"],
        plt.Ite(
            plt.LessThanInteger(OVar("x"), plt.Integer(0)),
            plt.Negate(OVar("x")),
            OVar("x"),
        ),
    )
    # maps an integer to a unicode code point and decodes it
    # reference: https://en.wikipedia.org/wiki/UTF-8#Encoding
    chr = OLambda(
        ["x"],
        plt.DecodeUtf8(
            plt.Ite(
                plt.LessThanInteger(OVar("x"), plt.Integer(0x0)),
                plt.TraceError("ValueError: chr() arg not in range(0x110000)"),
                plt.Ite(
                    plt.LessThanInteger(OVar("x"), plt.Integer(0x80)),
                    # encoding of 0x0 - 0x80
                    plt.ConsByteString(OVar("x"), plt.ByteString(b"")),
                    plt.Ite(
                        plt.LessThanInteger(OVar("x"), plt.Integer(0x800)),
                        # encoding of 0x80 - 0x800
                        plt.ConsByteString(
                            # we do bit manipulation using integer arithmetic here - nice
                            plt.AddInteger(
                                plt.Integer(0b110 << 5),
                                plt.DivideInteger(OVar("x"), plt.Integer(1 << 6)),
                            ),
                            plt.ConsByteString(
                                plt.AddInteger(
                                    plt.Integer(0b10 << 6),
                                    plt.ModInteger(OVar("x"), plt.Integer(1 << 6)),
                                ),
                                plt.ByteString(b""),
                            ),
                        ),
                        plt.Ite(
                            plt.LessThanInteger(OVar("x"), plt.Integer(0x10000)),
                            # encoding of 0x800 - 0x10000
                            plt.ConsByteString(
                                plt.AddInteger(
                                    plt.Integer(0b1110 << 4),
                                    plt.DivideInteger(OVar("x"), plt.Integer(1 << 12)),
                                ),
                                plt.ConsByteString(
                                    plt.AddInteger(
                                        plt.Integer(0b10 << 6),
                                        plt.DivideInteger(
                                            plt.ModInteger(
                                                OVar("x"), plt.Integer(1 << 12)
                                            ),
                                            plt.Integer(1 << 6),
                                        ),
                                    ),
                                    plt.ConsByteString(
                                        plt.AddInteger(
                                            plt.Integer(0b10 << 6),
                                            plt.ModInteger(
                                                OVar("x"), plt.Integer(1 << 6)
                                            ),
                                        ),
                                        plt.ByteString(b""),
                                    ),
                                ),
                            ),
                            plt.Ite(
                                plt.LessThanInteger(OVar("x"), plt.Integer(0x110000)),
                                # encoding of 0x10000 - 0x10FFF
                                plt.ConsByteString(
                                    plt.AddInteger(
                                        plt.Integer(0b11110 << 3),
                                        plt.DivideInteger(
                                            OVar("x"), plt.Integer(1 << 18)
                                        ),
                                    ),
                                    plt.ConsByteString(
                                        plt.AddInteger(
                                            plt.Integer(0b10 << 6),
                                            plt.DivideInteger(
                                                plt.ModInteger(
                                                    OVar("x"), plt.Integer(1 << 18)
                                                ),
                                                plt.Integer(1 << 12),
                                            ),
                                        ),
                                        plt.ConsByteString(
                                            plt.AddInteger(
                                                plt.Integer(0b10 << 6),
                                                plt.DivideInteger(
                                                    plt.ModInteger(
                                                        OVar("x"),
                                                        plt.Integer(1 << 12),
                                                    ),
                                                    plt.Integer(1 << 6),
                                                ),
                                            ),
                                            plt.ConsByteString(
                                                plt.AddInteger(
                                                    plt.Integer(0b10 << 6),
                                                    plt.ModInteger(
                                                        OVar("x"),
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
    breakpoint = OLambda(["_"], plt.NoneData())
    hex = OLambda(
        ["x"],
        plt.DecodeUtf8(
            OLet(
                [
                    (
                        "hexlist",
                        plt.RecFun(
                            OLambda(
                                ["f", "i"],
                                plt.Ite(
                                    plt.LessThanEqualsInteger(
                                        OVar("i"), plt.Integer(0)
                                    ),
                                    plt.EmptyIntegerList(),
                                    plt.MkCons(
                                        OLet(
                                            [
                                                (
                                                    "mod",
                                                    plt.ModInteger(
                                                        OVar("i"), plt.Integer(16)
                                                    ),
                                                ),
                                            ],
                                            plt.AddInteger(
                                                OVar("mod"),
                                                plt.IfThenElse(
                                                    plt.LessThanInteger(
                                                        OVar("mod"), plt.Integer(10)
                                                    ),
                                                    plt.Integer(ord("0")),
                                                    plt.Integer(ord("a") - 10),
                                                ),
                                            ),
                                        ),
                                        plt.Apply(
                                            OVar("f"),
                                            OVar("f"),
                                            plt.DivideInteger(
                                                OVar("i"), plt.Integer(16)
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "mkstr",
                        OLambda(
                            ["i"],
                            plt.FoldList(
                                plt.Apply(OVar("hexlist"), OVar("i")),
                                OLambda(
                                    ["b", "i"],
                                    plt.ConsByteString(OVar("i"), OVar("b")),
                                ),
                                plt.ByteString(b""),
                            ),
                        ),
                    ),
                ],
                plt.Ite(
                    plt.EqualsInteger(OVar("x"), plt.Integer(0)),
                    plt.ByteString(b"0x0"),
                    plt.Ite(
                        plt.LessThanInteger(OVar("x"), plt.Integer(0)),
                        plt.ConsByteString(
                            plt.Integer(ord("-")),
                            plt.AppendByteString(
                                plt.ByteString(b"0x"),
                                plt.Apply(OVar("mkstr"), plt.Negate(OVar("x"))),
                            ),
                        ),
                        plt.AppendByteString(
                            plt.ByteString(b"0x"),
                            plt.Apply(OVar("mkstr"), OVar("x")),
                        ),
                    ),
                ),
            )
        ),
    )
    len = "len"
    max = OLambda(
        ["xs"],
        plt.IteNullList(
            OVar("xs"),
            plt.TraceError("ValueError: max() arg is an empty sequence"),
            plt.FoldList(
                plt.TailList(OVar("xs")),
                OLambda(
                    ["x", "a"],
                    plt.IfThenElse(
                        plt.LessThanInteger(OVar("a"), OVar("x")),
                        OVar("x"),
                        OVar("a"),
                    ),
                ),
                plt.HeadList(OVar("xs")),
            ),
        ),
    )
    min = OLambda(
        ["xs"],
        plt.IteNullList(
            OVar("xs"),
            plt.TraceError("ValueError: min() arg is an empty sequence"),
            plt.FoldList(
                plt.TailList(OVar("xs")),
                OLambda(
                    ["x", "a"],
                    plt.IfThenElse(
                        plt.LessThanInteger(OVar("a"), OVar("x")),
                        OVar("a"),
                        OVar("x"),
                    ),
                ),
                plt.HeadList(OVar("xs")),
            ),
        ),
    )
    print = "print"
    # NOTE: only correctly defined for positive y
    pow = OLambda(
        ["x", "y"],
        plt.Ite(
            plt.LessThanInteger(OVar("y"), plt.Integer(0)),
            plt.TraceError("Negative exponentiation is not supported"),
            PowImpl(OVar("x"), OVar("y")),
        ),
    )
    oct = OLambda(
        ["x"],
        plt.DecodeUtf8(
            OLet(
                [
                    (
                        "octlist",
                        plt.RecFun(
                            OLambda(
                                ["f", "i"],
                                plt.Ite(
                                    plt.LessThanEqualsInteger(
                                        OVar("i"), plt.Integer(0)
                                    ),
                                    plt.EmptyIntegerList(),
                                    plt.MkCons(
                                        plt.AddInteger(
                                            plt.ModInteger(OVar("i"), plt.Integer(8)),
                                            plt.Integer(ord("0")),
                                        ),
                                        plt.Apply(
                                            OVar("f"),
                                            OVar("f"),
                                            plt.DivideInteger(
                                                OVar("i"), plt.Integer(8)
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "mkoct",
                        OLambda(
                            ["i"],
                            plt.FoldList(
                                plt.Apply(OVar("octlist"), OVar("i")),
                                OLambda(
                                    ["b", "i"],
                                    plt.ConsByteString(OVar("i"), OVar("b")),
                                ),
                                plt.ByteString(b""),
                            ),
                        ),
                    ),
                ],
                plt.Ite(
                    plt.EqualsInteger(OVar("x"), plt.Integer(0)),
                    plt.ByteString(b"0o0"),
                    plt.Ite(
                        plt.LessThanInteger(OVar("x"), plt.Integer(0)),
                        plt.ConsByteString(
                            plt.Integer(ord("-")),
                            plt.AppendByteString(
                                plt.ByteString(b"0o"),
                                plt.Apply(OVar("mkoct"), plt.Negate(OVar("x"))),
                            ),
                        ),
                        plt.AppendByteString(
                            plt.ByteString(b"0o"),
                            plt.Apply(OVar("mkoct"), OVar("x")),
                        ),
                    ),
                ),
            )
        ),
    )
    range = OLambda(
        ["limit"],
        plt.Range(OVar("limit")),
    )
    reversed = "reversed"
    sum = OLambda(
        ["xs"],
        plt.FoldList(
            OVar("xs"), plt.BuiltIn(uplc.BuiltInFun.AddInteger), plt.Integer(0)
        ),
    )


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
    PythonBuiltIn.print: InstanceType(PolymorphicFunctionType(PrintImpl())),
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
