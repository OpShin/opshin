from typing import Optional
from enum import Enum

from ..util import CompilingNodeTransformer
from ..typed_ast import *

"""
Checks that there was an import of dataclass if there are any class definitions
"""


@dataclass(frozen=True, unsafe_hash=True)
class HashType(ClassType):
    """A pseudo class that is the result of python hash functions that need a 'digest' call"""

    def attribute_type(self, attr) -> "Type":
        if attr == "digest":
            return InstanceType(FunctionType(frozenlist([]), ByteStringInstanceType))
        raise NotImplementedError("HashType only has attribute 'digest'")

    def attribute(self, attr) -> plt.AST:
        if attr == "digest":
            return plt.Lambda(["self"], plt.Var("self"))
        raise NotImplementedError("HashType only has attribute 'digest'")

    def __ge__(self, other):
        return isinstance(other, HashType)


HashInstanceType = InstanceType(HashType())


class PythonHashlib(Enum):
    sha256 = plt.Lambda(["x", "_"], plt.Lambda(["_"], plt.Sha2_256(plt.Var("x"))))
    sha3_256 = plt.Lambda(["x", "_"], plt.Lambda(["_"], plt.Sha3_256(plt.Var("x"))))
    blake2b = plt.Lambda(["x", "_"], plt.Lambda(["_"], plt.Blake2b_256(plt.Var("x"))))


PythonHashlibTypes = {
    PythonHashlib.sha256: InstanceType(
        FunctionType(
            frozenlist([ByteStringInstanceType]),
            HashInstanceType,
        )
    ),
    PythonHashlib.sha3_256: InstanceType(
        FunctionType(
            frozenlist([ByteStringInstanceType]),
            HashInstanceType,
        )
    ),
    PythonHashlib.blake2b: InstanceType(
        FunctionType(
            frozenlist([ByteStringInstanceType]),
            HashInstanceType,
        )
    ),
}


class RewriteImportHashlib(CompilingNodeTransformer):
    step = "Resolving imports and usage of hashlib"

    imports_hashlib = False

    def visit_ImportFrom(self, node: ImportFrom) -> typing.List[AST]:
        if node.module != "hashlib":
            return node
        additional_assigns = []
        for n in node.names:
            imported_fun = None
            for h in PythonHashlib:
                if h.name == n.name:
                    imported_fun = h
            assert (
                imported_fun is not None
            ), f"Unsupported function import from hashlib '{n.name}"
            typ = PythonHashlibTypes[imported_fun]
            imported_name = n.name if n.asname is None else n.asname
            additional_assigns.append(
                TypedAssign(
                    targets=[TypedName(id=imported_name, typ=typ, ctx=Store())],
                    value=RawPlutoExpr(
                        typ=typ, expr=plt.Lambda(["_"], imported_fun.value)
                    ),
                )
            )
        return additional_assigns
