from ast import *
from copy import copy
from collections import defaultdict

from ..util import CompilingNodeTransformer, CompilingNodeVisitor

"""
Rewrites all variable names to a minimal length equivalent
"""


class NameCollector(CompilingNodeVisitor):
    step = "Collecting occuring variable names"

    def __init__(self):
        self.vars = defaultdict(int)

    def visit_Name(self, node: Name) -> None:
        self.vars[node.id] += 1

    def visit_ClassDef(self, node: ClassDef):
        self.vars[node.name] += 1
        # ignore the content (i.e. attribute names) of class definitions

    def visit_FunctionDef(self, node: FunctionDef):
        self.vars[node.name] += 1
        for a in node.args.args:
            # ignore type hints
            self.vars[a.arg] += 1
        for s in node.body:
            self.visit(s)


def bs_from_int(i: int):
    hex_str = f"{i:x}"
    if len(hex_str) % 2 == 1:
        hex_str = "0" + hex_str
    return bytes.fromhex(hex_str)


class OptimizeVarlen(CompilingNodeTransformer):
    step = "Reducing the length of variable names"

    varmap = None

    def visit_Module(self, node: Module) -> Module:
        # collect all variable names
        collector = NameCollector()
        collector.visit(node)
        # sort by most used
        varmap = {}
        varnames = sorted(collector.vars.items(), key=lambda x: x[1], reverse=True)
        for i, (v, _) in enumerate(varnames):
            varmap[v] = bs_from_int(i)
        self.varmap = varmap
        node_cp = copy(node)
        node_cp.body = [self.visit(s) for s in node.body]
        return node_cp

    def visit_Name(self, node: Name) -> Name:
        nc = copy(node)
        nc.id = self.varmap[node.id]
        return nc

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        node_cp = copy(node)
        node_cp.name = self.varmap[node.name]
        # ignore the content of class definitions
        return node_cp

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        node_cp = copy(node)
        node_cp.name = self.varmap[node.name]
        node_cp.args = copy(node.args)
        node_cp.args.args = []
        for a in node.args.args:
            a_cp = copy(a)
            a_cp.arg = self.varmap[a.arg]
            node_cp.args.args.append(a_cp)
        node_cp.body = [self.visit(s) for s in node.body]
        return node_cp
