import re
from copy import copy
from typing import Optional
from enum import Enum

from ..type_inference import INITIAL_SCOPE
from ..util import CompilingNodeTransformer
from ..typed_ast import *

"""
Injects the integrity checker function if it is imported
"""

FunctionName = "check_integrity"


class IntegrityCheckImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 1
        ), f"'integrity_check' takes only one argument, but {len(args)} were given"
        typ = args[0]
        assert isinstance(typ, InstanceType), "Can only check integrity of instances"
        assert any(
            isinstance(typ.typ, t) for t in (RecordType, UnionType)
        ), "Can only check integrity of PlutusData and Union types"
        return FunctionType(args, NoneInstanceType)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(arg, InstanceType), "Can only check integrity of instances"
        return OLambda(
            ["x"],
            plt.Ite(
                plt.EqualsData(
                    OVar("x"),
                    plt.Apply(arg.typ.copy_only_attributes(), OVar("x")),
                ),
                plt.Unit(),
                plt.TraceError("ValueError: datum integrity check failed"),
            ),
        )


class RewriteImportIntegrityCheck(CompilingNodeTransformer):
    step = "Resolving imports and usage of integrity check"

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[AST]:
        if node.module != "opshin.std.integrity":
            return node
        for n in node.names:
            assert (
                n.name == FunctionName
            ), "Imports something other from the integrity check than the integrity check builtin"
            renamed = n.asname if n.asname is not None else n.name
            INITIAL_SCOPE[renamed] = InstanceType(
                PolymorphicFunctionType(IntegrityCheckImpl())
            )
        return None
