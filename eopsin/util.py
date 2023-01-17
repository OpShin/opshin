from enum import Enum

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
}


class TypedNodeTransformer(NodeTransformer):
    def visit(self, node):
        """Visit a node."""
        node_class_name = node.__class__.__name__
        if node_class_name.startswith("Typed"):
            node_class_name = node_class_name[len("Typed") :]
        method = "visit_" + node_class_name
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)


class TypedNodeVisitor(NodeVisitor):
    def visit(self, node):
        """Visit a node."""
        node_class_name = node.__class__.__name__
        if node_class_name.startswith("Typed"):
            node_class_name = node_class_name[len("Typed") :]
        method = "visit_" + node_class_name
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)
