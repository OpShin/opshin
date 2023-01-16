from ast import *
from copy import copy
from collections import defaultdict

"""
Rewrites all variable names to a minimal length equivalent
"""


class NameCollector(NodeVisitor):
    def __init__(self):
        self.vars = defaultdict(int)

    def visit_Name(self, node: Name) -> None:
        self.vars[node.id] += 1


def bs_from_int(i: int):
    hex_str = f"{i:x}"
    if len(hex_str) % 2 == 1:
        hex_str = "0" + hex_str
    return bytes.fromhex(hex_str)


class OptimizeVarlen(NodeTransformer):

    varmap = None

    def visit_Module(self, node: Module) -> Module:
        # collect all variable names
        collector = NameCollector()
        collector.visit(node)
        # sort by most used
        varmap = {}
        varnames = sorted(collector.vars.items(), key=lambda x: x[1], reverse=True)
        for i, v in enumerate(varnames):
            varmap[v] = bs_from_int(i)
        self.varmap = varmap
        return node

    def visit_Name(self, node: Name) -> Name:
        nc = copy(node)
        nc.id = self.varmap[nc.id]
        return nc
