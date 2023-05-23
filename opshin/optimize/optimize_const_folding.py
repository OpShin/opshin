from copy import copy

from ast import *

try:
    unparse
except NameError:
    from astunparse import unparse

from ..util import CompilingNodeTransformer, CompilingNodeVisitor
from ..type_inference import INITIAL_SCOPE

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

SAFE_GLOBALS_LIST = [
    abs,
    all,
    any,
    ascii,
    bin,
    bool,
    bytes,
    bytearray,
    callable,
    chr,
    classmethod,
    compile,
    complex,
    delattr,
    dict,
    dir,
    divmod,
    enumerate,
    filter,
    float,
    format,
    frozenset,
    getattr,
    hasattr,
    hash,
    hex,
    id,
    input,
    int,
    isinstance,
    issubclass,
    iter,
    len,
    list,
    map,
    max,
    min,
    next,
    object,
    oct,
    open,
    ord,
    pow,
    print,
    property,
    range,
    repr,
    reversed,
    round,
    set,
    setattr,
    slice,
    sorted,
    staticmethod,
    str,
    sum,
    super,
    tuple,
    type,
    vars,
    zip,
]
SAFE_GLOBALS = {x.__name__: x for x in SAFE_GLOBALS_LIST}


class ShallowNameDefCollector(CompilingNodeVisitor):
    step = "Collecting occuring variable names"

    def __init__(self):
        self.vars = set()

    def visit_Name(self, node: Name) -> None:
        if isinstance(node.ctx, Store):
            self.vars.add(node.id)

    def visit_ClassDef(self, node: ClassDef):
        self.vars.add(node.name)
        # ignore the content (i.e. attribute names) of class definitions

    def visit_FunctionDef(self, node: FunctionDef):
        self.vars.add(node.name)
        # ignore the recursive stuff


class OptimizeConstantFolding(CompilingNodeTransformer):
    step = "Constant folding"

    def __init__(self):
        self.scopes = [set(INITIAL_SCOPE.keys()).difference(SAFE_GLOBALS.keys())]

    def enter_scope(self):
        self.scopes.append(set())

    def add_var(self, var: str):
        self.scopes[-1].add(var)

    def visible_vars(self):
        res_set = set()
        for s in self.scopes:
            res_set.update(s)
        return res_set

    def exit_scope(self):
        self.scopes.pop(-1)

    def visit_Module(self, node: Module) -> Module:
        self.enter_scope()
        def_vars_collector = ShallowNameDefCollector()
        for s in node.body:
            def_vars_collector.visit(s)
        def_vars = def_vars_collector.vars
        for def_var in def_vars:
            self.add_var(def_var)
        res = self.generic_visit(node)
        self.exit_scope()
        return res

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        self.add_var(node.name)
        self.enter_scope()
        for arg in node.args.args:
            self.add_var(arg.arg)
        def_vars_collector = ShallowNameDefCollector()
        for s in node.body:
            def_vars_collector.visit(s)
        def_vars = def_vars_collector.vars
        for def_var in def_vars:
            self.add_var(def_var)
        res_node = self.generic_visit(node)
        self.exit_scope()
        return res_node

    def generic_visit(self, node: AST):
        node = super().generic_visit(node)
        if not isinstance(node, expr):
            # only evaluate expressions, not statements
            return node
        if isinstance(node, Constant):
            # prevents unneccessary computations
            return node
        node_source = unparse(node)
        if "print(" in node_source:
            # do not optimize away print statements
            return node
        overwritten_vars = self.visible_vars()

        def err():
            raise ValueError("Was overwritten!")

        non_overwritten_globals = {
            k: (v if k not in overwritten_vars else err)
            for k, v in SAFE_GLOBALS.items()
        }
        try:
            # TODO we can add preceding plutusdata definitions here!
            node_eval = eval(node_source, non_overwritten_globals, {})
        except Exception as e:
            return node

        if any(isinstance(node_eval, t) for t in ACCEPTED_ATOMIC_TYPES + [list, dict]):
            new_node = Constant(node_eval, None)
            copy_location(new_node, node)
            return new_node
        return node
