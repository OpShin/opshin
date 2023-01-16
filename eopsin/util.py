from enum import Enum

import pluthon as plt

from .typed_ast import *


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
    sha256 = plt.Lambda(["x", "_"], plt.Sha2_256(plt.Var("x")))
    sha3_256 = plt.Lambda(["x", "_"], plt.Sha3_256(plt.Var("x")))
    blake2b = plt.Lambda(["x", "_"], plt.Blake2b_256(plt.Var("x")))


HashDigestType = RecordType(
    Record(
        "HashDigest",
        0,
        [("digest", InstanceType(FunctionType([], ByteStringInstanceType)))],
    )
)


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
            [ByteStringType],
            HashDigestType,
        )
    ),
    PythonBuiltIn.sha3_256: InstanceType(
        FunctionType(
            [ByteStringType],
            HashDigestType,
        )
    ),
    PythonBuiltIn.blake2b: InstanceType(
        FunctionType(
            [ByteStringType],
            HashDigestType,
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
