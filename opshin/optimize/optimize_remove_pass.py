from ast import *

from ..util import CompilingNodeTransformer

"""
Removes pass statements
"""


class OptimizeRemovePass(CompilingNodeTransformer):
    step = "Removing occurrences of 'pass'"

    def visit_Pass(self, node: Pass):
        return None
