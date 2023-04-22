from ast import *

try:
    unparse
except NameError:
    from astunparse import unparse

from ..util import CompilingNodeTransformer

"""
Pre-evaluates constant statements
"""

ACCEPTED_ATOMIC_TYPES = [
    int,
    str,
    bytes,
    type(None),
    bool,
]


class OptimizeConstantFolding(CompilingNodeTransformer):
    step = "Constant folding"

    def generic_visit(self, node: AST):
        node = super().generic_visit(node)
        if not isinstance(node, expr):
            # only evaluate expressions, not statements
            return node
        if isinstance(node, Constant):
            # prevents unneccessary computations
            return node
        node_source = unparse(node)
        try:
            # TODO we can add preceding plutusdata definitions here!
            node_eval = eval(node_source, globals(), {})
        except Exception as e:
            return node

        def rec_dump(c):
            if any(isinstance(c, a) for a in ACCEPTED_ATOMIC_TYPES):
                new_node = Constant(c)
                copy_location(new_node, node)
                return new_node
            if isinstance(c, list):
                return List((rec_dump(ce) for ce in c), Load())
            if isinstance(c, dict):
                return Dict(
                    (rec_dump(ce) for ce in c.keys()),
                    (rec_dump(ce) for ce in c.values()),
                )

        if any(isinstance(node_eval, t) for t in ACCEPTED_ATOMIC_TYPES + [list, dict]):
            return rec_dump(node_eval)
        return node
