from ast import *
from copy import copy
from collections import defaultdict

from ..type_inference import INITIAL_SCOPE, PolymorphicFunctionInstanceType
from ..util import CompilingNodeTransformer, CompilingNodeVisitor

"""
Rewrites all variable names to point to the definition in the nearest enclosing scope
"""


class ShallowNameDefCollector(CompilingNodeVisitor):
    step = "Collecting occuring variable names"

    def __init__(self):
        self.vars = set()

    def visit_Name(self, node: Name) -> None:
        if isinstance(node.ctx, Store) or isinstance(
            node.typ, PolymorphicFunctionInstanceType
        ):
            self.vars.add(node.id)

    def visit_ClassDef(self, node: ClassDef):
        self.vars.add(node.name)
        # ignore the content (i.e. attribute names) of class definitions

    def visit_FunctionDef(self, node: FunctionDef):
        self.vars.add(node.name)
        # ignore the recursive stuff


class RewriteScoping(CompilingNodeTransformer):
    step = "Rewrite all variables to inambiguously point to the definition in the nearest enclosing scope"

    def __init__(self):
        self.latest_scope_id = 0
        self.scopes = [(set(INITIAL_SCOPE.keys()), -1)]

    def variable_scope_id(self, name: str) -> int:
        """find the id of the scope in which this variable is defined (closest to its usage)"""
        name = name
        for scope, scope_id in reversed(self.scopes):
            if name in scope:
                return scope_id
        raise NameError(
            f"free variable '{name}' referenced before assignment in enclosing scope"
        )

    def enter_scope(self):
        self.scopes.append((set(), self.latest_scope_id))
        self.latest_scope_id += 1

    def exit_scope(self):
        self.scopes.pop()

    def set_variable_scope(self, name: str):
        self.scopes[-1][0].add(name)

    def map_name(self, name: str):
        scope_id = self.variable_scope_id(name)
        if scope_id == -1:
            # do not rewrite Dict, Union, etc
            return name
        return f"{name}_{scope_id}"

    def visit_Module(self, node: Module) -> Module:
        node_cp = copy(node)
        self.enter_scope()
        # vars defined in this scope
        shallow_node_def_collector = ShallowNameDefCollector()
        for s in node.body:
            shallow_node_def_collector.visit(s)
        vars_def = shallow_node_def_collector.vars
        for var_name in vars_def:
            self.set_variable_scope(var_name)
        node_cp.body = [self.visit(s) for s in node.body]
        return node_cp

    def visit_Name(self, node: Name) -> Name:
        nc = copy(node)
        # setting is handled in either enclosing module or function
        nc.id = self.map_name(node.id)
        return nc

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        node_cp = copy(node)
        # setting is handled in either enclosing module or function
        node_cp.name = self.map_name(node.name)
        # ignore the content of class definitions
        return node_cp

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        node_cp = copy(node)
        # setting is handled in either enclosing module or function
        node_cp.name = self.map_name(node.name)
        self.enter_scope()
        node_cp.args = copy(node.args)
        node_cp.args.args = []
        # args are defined in this scope
        for a in node.args.args:
            a_cp = copy(a)
            self.set_variable_scope(a.arg)
            a_cp.arg = self.map_name(a.arg)
            node_cp.args.args.append(a_cp)
        # vars defined in this scope
        shallow_node_def_collector = ShallowNameDefCollector()
        for s in node.body:
            shallow_node_def_collector.visit(s)
        vars_def = shallow_node_def_collector.vars
        for var_name in vars_def:
            self.set_variable_scope(var_name)
        # map all vars and recurse
        node_cp.body = [self.visit(s) for s in node.body]
        self.exit_scope()
        return node_cp
