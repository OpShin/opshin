import ast

from enum import Enum, auto

from .typed_ast import *

import pluthon as plt


class RawPlutoExpr(typedexpr):
    typ: Type
    expr: plt.AST


class PythonBuiltIn(Enum):
    print = plt.Lambda(
        ["x", "_"],
        plt.Trace(plt.Var("x"), plt.NoneData()),
    )
    range = plt.Lambda(
        ["limit", "_"],
        plt.Range(plt.Var("limit")),
    )
    sha256 = plt.Lambda(["x", "_"], plt.Lambda(["_"], plt.Sha2_256(plt.Var("x"))))
    sha3_256 = plt.Lambda(["x", "_"], plt.Lambda(["_"], plt.Sha3_256(plt.Var("x"))))
    blake2b = plt.Lambda(["x", "_"], plt.Lambda(["_"], plt.Blake2b_256(plt.Var("x"))))
    len = auto()


@dataclass(frozen=True, unsafe_hash=True)
class HashType(ClassType):
    """A pseudo class that is the result of python hash functions that need a 'digest' call"""

    def attribute_type(self, attr) -> "Type":
        if attr == "digest":
            return InstanceType(FunctionType([], ByteStringInstanceType))
        raise NotImplementedError("HashType only has attribute 'digest'")

    def attribute(self, attr) -> plt.AST:
        if attr == "digest":
            return plt.Lambda(["self"], plt.Var("self"))
        raise NotImplementedError("HashType only has attribute 'digest'")


HashInstanceType = InstanceType(HashType())


class Len(PolymorphicFunction):
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


PythonBuiltInTypes = {
    PythonBuiltIn.print: InstanceType(
        FunctionType([StringInstanceType], NoneInstanceType)
    ),
    PythonBuiltIn.range: InstanceType(
        FunctionType(
            [IntegerInstanceType],
            InstanceType(ListType(IntegerInstanceType)),
        )
    ),
    PythonBuiltIn.sha256: InstanceType(
        FunctionType(
            [ByteStringInstanceType],
            HashInstanceType,
        )
    ),
    PythonBuiltIn.sha3_256: InstanceType(
        FunctionType(
            [ByteStringInstanceType],
            HashInstanceType,
        )
    ),
    PythonBuiltIn.blake2b: InstanceType(
        FunctionType(
            [ByteStringInstanceType],
            HashInstanceType,
        )
    ),
    PythonBuiltIn.len: InstanceType(PolymorphicFunctionType(Len())),
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
