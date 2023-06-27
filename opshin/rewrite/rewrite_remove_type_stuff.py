from typing import Optional

from ..typed_ast import TypedAssign, ClassType
from ..util import CompilingNodeTransformer

"""
Remove class reassignments without constructors
"""


class RewriteRemoveTypeStuff(CompilingNodeTransformer):
    step = "Removing class re-assignments"

    def visit_Assign(self, node: TypedAssign) -> Optional[TypedAssign]:
        assert (
            len(node.targets) == 1
        ), "Assignments to more than one variable not supported yet"
        try:
            if isinstance(node.value.typ, ClassType):
                node.value.typ.constr()
        except NotImplementedError:
            # The type does not have a constructor and the constructor can hence not be passed on
            return None
        except AttributeError:
            # untyped attributes are fine too
            pass
        return node
