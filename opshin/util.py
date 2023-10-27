import typing

import ast
from dataclasses import dataclass

import pycardano
from frozendict import frozendict
from frozenlist2 import frozenlist

import uplc.ast as uplc
import pluthon as plt
from hashlib import sha256


def distinct(xs: list):
    """Returns true iff the list consists of distinct elements"""
    return len(xs) == len(set(xs))


class TypedNodeTransformer(ast.NodeTransformer):
    def visit(self, node):
        """Visit a node."""
        node_class_name = node.__class__.__name__
        if node_class_name.startswith("Typed"):
            node_class_name = node_class_name[len("Typed") :]
        method = "visit_" + node_class_name
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)


class TypedNodeVisitor(ast.NodeVisitor):
    def visit(self, node):
        """Visit a node."""
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
            {"compose": lambda self: structure},
        )
        AdHocPattern = dataclass(AdHocPattern)

        _patterns_cached[structure_serialized] = AdHocPattern()
    return _patterns_cached[structure_serialized]


def patternize(method):
    def wrapped(*args, **kwargs):
        return make_pattern(method(*args, **kwargs))

    return wrapped
