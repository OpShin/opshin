import ast

from ..typed_util import ScopedSequenceNodeTransformer
from .analyze_integrity import is_integrity_call


class OptimizeRemoveCheckedIntegrityChecks(ScopedSequenceNodeTransformer):
    """Remove integrity checks whose arguments have already passed integrity checks."""

    step = "Removing redundant integrity checks"

    def visit_Expr(self, node: ast.Expr):
        if (
            is_integrity_call(node.value)
            and len(node.value.args) == 1
            and node.value.args[0].integrity_checked
        ):
            return None
        return node
