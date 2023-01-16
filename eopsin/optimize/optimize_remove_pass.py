from ast import *
from copy import copy

from ..util import TypedNodeTransformer

"""
Removes pass statements
"""


class OptimizeRemovePass(TypedNodeTransformer):
    def visit_Pass(self, node: Pass):
        return None
