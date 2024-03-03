from _ast import Name, Store, ClassDef, FunctionDef, Load
from collections import defaultdict
from copy import copy, deepcopy
import logging

import typing

import ast
from dataclasses import dataclass

import pycardano
from frozendict import frozendict
from frozenlist2 import frozenlist

import uplc.ast as uplc
import pluthon as plt
from hashlib import sha256

OPSHIN_LOGGER = logging.getLogger("opshin")
OPSHIN_LOG_HANDLER = logging.StreamHandler()
OPSHIN_LOGGER.addHandler(OPSHIN_LOG_HANDLER)


class FileContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.

    The information is about the currently inspected AST node.
    The information needs to be updated inside the NodeTransformer and NodeVisitor classes.
    """

    file_name = "unknown"
    node: ast.AST = None

    def filter(self, record):

        if self.node is None:
            record.lineno = 1
            record.col_offset = 0
            record.end_lineno = 1
            record.end_col_offset = 0
        else:
            record.lineno = self.node.lineno
            record.col_offset = self.node.col_offset
            record.end_lineno = self.node.end_lineno
            record.end_col_offset = self.node.end_col_offset
        return True


OPSHIN_LOG_CONTEXT_FILTER = FileContextFilter()
OPSHIN_LOG_HANDLER.addFilter(OPSHIN_LOG_CONTEXT_FILTER)


def distinct(xs: list):
    """Returns true iff the list consists of distinct elements"""
    return len(xs) == len(set(xs))


class TypedNodeTransformer(ast.NodeTransformer):
    def visit(self, node):
        """Visit a node."""
        OPSHIN_LOG_CONTEXT_FILTER.node = node
        node_class_name = node.__class__.__name__
        if node_class_name.startswith("Typed"):
            node_class_name = node_class_name[len("Typed") :]
        method = "visit_" + node_class_name
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)


class TypedNodeVisitor(ast.NodeVisitor):
    def visit(self, node):
        """Visit a node."""
        OPSHIN_LOG_CONTEXT_FILTER.node = node
        node_class_name = node.__class__.__name__
        if node_class_name.startswith("Typed"):
            node_class_name = node_class_name[len("Typed") :]
        method = "visit_" + node_class_name
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)


class CompilerError(Exception):
    def __init__(self, orig_err: Exception, node: ast.AST, compilation_step: str):
        self.orig_err = orig_err
        self.node = node
        self.compilation_step = compilation_step


class CompilingNodeTransformer(TypedNodeTransformer):
    step = "Node transformation"

    def visit(self, node):
        OPSHIN_LOG_CONTEXT_FILTER.node = node
        try:
            return super().visit(node)
        except Exception as e:
            if isinstance(e, CompilerError):
                raise e
            raise CompilerError(e, node, self.step)


class NoOp(CompilingNodeTransformer):
    """A variation of the Compiling Node transformer that performs no changes"""

    pass


class CompilingNodeVisitor(TypedNodeVisitor):
    step = "Node visiting"

    def visit(self, node):
        try:
            return super().visit(node)
        except Exception as e:
            if isinstance(e, CompilerError):
                raise e
            raise CompilerError(e, node, self.step)


def data_from_json(j: typing.Dict[str, typing.Any]) -> uplc.PlutusData:
    if "bytes" in j:
        return uplc.PlutusByteString(bytes.fromhex(j["bytes"]))
    if "int" in j:
        return uplc.PlutusInteger(int(j["int"]))
    if "list" in j:
        return uplc.PlutusList(frozenlist(list(map(data_from_json, j["list"]))))
    if "map" in j:
        return uplc.PlutusMap(
            frozendict(
                {data_from_json(d["k"]): data_from_json(d["v"]) for d in j["map"]}
            )
        )
    if "constructor" in j and "fields" in j:
        return uplc.PlutusConstr(
            j["constructor"], frozenlist(list(map(data_from_json, j["fields"])))
        )
    raise NotImplementedError(f"Unknown datum representation {j}")


def datum_to_cbor(d: pycardano.Datum) -> bytes:
    return pycardano.PlutusData.to_cbor(d)


def datum_to_json(d: pycardano.Datum) -> str:
    return pycardano.PlutusData.to_json(d)


def custom_fix_missing_locations(node, parent=None):
    """
    Works like ast.fix_missing_location but forces it onto everything
    """

    def _fix(node, lineno, col_offset, end_lineno, end_col_offset):
        if getattr(node, "lineno", None) is None:
            node.lineno = lineno
        else:
            lineno = node.lineno
        if getattr(node, "end_lineno", None) is None:
            node.end_lineno = end_lineno
        else:
            end_lineno = node.end_lineno
        if getattr(node, "col_offset", None) is None:
            node.col_offset = col_offset
        else:
            col_offset = node.col_offset
        if getattr(node, "end_col_offset", None) is None:
            node.end_col_offset = end_col_offset
        else:
            end_col_offset = node.end_col_offset
        for child in ast.iter_child_nodes(node):
            _fix(child, lineno, col_offset, end_lineno, end_col_offset)

    lineno, col_offset, end_lineno, end_col_offset = (
        getattr(parent, "lineno", 1),
        getattr(parent, "col_offset", 0),
        getattr(parent, "end_lineno", 1),
        getattr(parent, "end_col_offset", 0),
    )
    _fix(node, lineno, col_offset, end_lineno, end_col_offset)
    return node


_patterns_cached = {}


def make_pattern(structure: plt.AST) -> plt.Pattern:
    """Creates a shared pattern from the given lambda, cached so that it is re-used in subsequent calls"""
    structure_serialized = structure.dumps()
    if _patterns_cached.get(structure_serialized) is None:
        # @dataclass
        # class AdHocPattern(plt.Pattern):

        #     def compose(self):
        #         return structure
        AdHocPattern = type(
            f"AdHocPattern_{sha256(structure_serialized.encode()).digest().hex()}",
            (plt.Pattern,),
            {"compose": lambda self: deepcopy(structure)},
        )
        AdHocPattern = dataclass(AdHocPattern)

        _patterns_cached[structure_serialized] = AdHocPattern()
    return deepcopy(_patterns_cached[structure_serialized])


def patternize(method):
    def wrapped(*args, **kwargs):
        return make_pattern(method(*args, **kwargs))

    return wrapped


def force_params(lmd: plt.Lambda) -> plt.Lambda:
    if isinstance(lmd, plt.Lambda):
        return plt.Lambda(
            lmd.vars, plt.Let([(v, plt.Force(plt.Var(v))) for v in lmd.vars], lmd.term)
        )
    if isinstance(lmd, plt.Pattern):
        return make_pattern(force_params(lmd.compose()))


class NameWriteCollector(CompilingNodeVisitor):
    step = "Collecting variables that are written"

    def __init__(self):
        self.written = defaultdict(int)

    def visit_Name(self, node: Name) -> None:
        if isinstance(node.ctx, Store):
            self.written[node.id] += 1

    def visit_ClassDef(self, node: ClassDef):
        # ignore the content (i.e. attribute names) of class definitions
        self.written[node.name] += 1
        pass

    def visit_FunctionDef(self, node: FunctionDef):
        # ignore the type hints of function arguments
        self.written[node.name] += 1
        for a in node.args.args:
            self.written[a.arg] += 1
        for s in node.body:
            self.visit(s)


def written_vars(node):
    """
    Returns all variable names written to in this node
    """
    collector = NameWriteCollector()
    collector.visit(node)
    return sorted(collector.written.keys())


class NameReadCollector(CompilingNodeVisitor):
    step = "Collecting variables that are read"

    def __init__(self):
        self.read = defaultdict(int)

    def visit_AnnAssign(self, node) -> None:
        # ignore annotations of variables
        self.visit(node.value)
        self.visit(node.target)

    def visit_FunctionDef(self, node) -> None:
        # ignore annotations of paramters and return
        for b in node.body:
            self.visit(b)

    def visit_Name(self, node: Name) -> None:
        if isinstance(node.ctx, Load):
            self.read[node.id] += 1

    def visit_ClassDef(self, node: ClassDef):
        # ignore the content (i.e. attribute names) of class definitions
        pass


def read_vars(node):
    """
    Returns all variable names read to in this node
    """
    collector = NameReadCollector()
    collector.visit(node)
    return sorted(collector.read.keys())


def all_vars(node):
    return sorted(set(read_vars(node) + written_vars(node)))


def externally_bound_vars(node: FunctionDef):
    """A superset of the variables bound from an outer scope"""
    return sorted(set(read_vars(node)) - set(written_vars(node)) - {"isinstance"})


def opshin_name_scheme_compatible_varname(n: str):
    return f"1{n}"


def OVar(name: str):
    return plt.Var(opshin_name_scheme_compatible_varname(name))


def OLambda(names: typing.List[str], term: plt.AST):
    return plt.Lambda([opshin_name_scheme_compatible_varname(x) for x in names], term)


def OLet(bindings: typing.List[typing.Tuple[str, plt.AST]], term: plt.AST):
    return plt.Let(
        [(opshin_name_scheme_compatible_varname(n), t) for n, t in bindings], term
    )


def SafeLambda(vars: typing.List[str], term: plt.AST) -> plt.Lambda:
    if not vars:
        return plt.Lambda(["0_"], term)
    return plt.Lambda(vars, term)


def SafeOLambda(vars: typing.List[str], term: plt.AST) -> plt.Lambda:
    if not vars:
        return OLambda(["0_"], term)
    return OLambda(vars, term)


def SafeApply(term: plt.AST, *vars: typing.List[plt.AST]) -> plt.Apply:
    if not vars:
        return plt.Apply(term, plt.Delay(plt.Unit()))
    return plt.Apply(term, *vars)
