import typing
from _ast import ImportFrom, AST, Store
from dataclasses import dataclass
from enum import Enum, auto
import pluthon as plt

from frozenlist2 import frozenlist

from ..typed_ast import *
from ..type_impls import (
    ClassType,
    InstanceType,
    ByteStringInstanceType,
    FunctionType,
    AtomicType,
    UnitType,
)
from ..util import CompilingNodeTransformer, force_params

"""
Checks that there was an import of dataclass if there are any class definitions
"""


@dataclass(frozen=True, unsafe_hash=True)
class BLS12381G1ElementType(ClassType):
    def python_type(self):
        return "BLS12381G1Element"


@dataclass(frozen=True, unsafe_hash=True)
class BLS12381G2ElementType(ClassType):
    def python_type(self):
        return "BLS12381G2Element"


@dataclass(frozen=True, unsafe_hash=True)
class BLS12381MlresultType(ClassType):
    def python_type(self):
        return "BLS12381MillerLoopResult"


BLS12_381_ENTRIES = {
    x.python_type(): x
    for x in (
        BLS12381G1ElementType(),
        BLS12381G2ElementType(),
        BLS12381MlresultType(),
    )
}


class RewriteImportBLS12381(CompilingNodeTransformer):
    step = "Resolving imports and usage of std.bls12_381"

    def visit_ImportFrom(self, node: ImportFrom) -> typing.Union[typing.List[AST], AST]:
        if node.module != "opshin.std.bls12_381":
            return node
        additional_assigns = []
        for n in node.names:
            imported_type = BLS12_381_ENTRIES.get(n.name)
            assert (
                imported_type is not None
            ), f"Unsupported type import from bls12_381 '{n.name}"
            imported_name = n.name if n.asname is None else n.asname
            additional_assigns.append(
                TypedAssign(
                    targets=[
                        TypedName(id=imported_name, typ=imported_type, ctx=Store())
                    ],
                    value=RawPlutoExpr(expr=plt.Unit(), typ=UnitType()),
                )
            )
        return additional_assigns
