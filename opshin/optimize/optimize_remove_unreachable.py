from ..typed_util import ScopedSequenceNodeTransformer

"""
Removes statements that are unreachable because a previous statement in the same
sequence is known not to fall through.
"""


class OptimizeRemoveUnreachable(ScopedSequenceNodeTransformer):
    step = "Removing unreachable statements"

    def visit_sequence(self, statements):
        visited = []
        for stmt in statements:
            if stmt is None:
                continue
            stmt_cp = self.visit(stmt)
            if stmt_cp is None:
                continue
            visited.append(stmt_cp)
            if not getattr(stmt_cp, "can_fall_through", True):
                break
        return visited
