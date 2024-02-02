from typing import Optional

from ..typed_ast import (
    TypedAssign,
    ClassType,
    InstanceType,
    PolymorphicFunctionType,
    TypeInferenceError,
)
from ..util import CompilingNodeTransformer

"""
Remove class reassignments without constructors and polymorphic function reassignments

Both of these are only present during the type inference and are discarded or generated in-place during compilation.
"""


class RewriteRemoveTypeStuff(CompilingNodeTransformer):
    step = "Removing class and polymorphic function re-assignments"

    def visit_Assign(self, node: TypedAssign) -> Optional[TypedAssign]:
        assert (
            len(node.targets) == 1
        ), "Assignments to more than one variable not supported yet"
        try:
            if isinstance(node.value.typ, ClassType):
                try:
                    typ = node.value.typ.constr_type()
                except TypeInferenceError:
                    # no constr_type is also fine
                    return None
            else:
                typ = node.value.typ
            if isinstance(typ, InstanceType) and isinstance(
                typ.typ, PolymorphicFunctionType
            ):
                return None
        except AttributeError:
            # untyped attributes are fine too
            pass
        return node
