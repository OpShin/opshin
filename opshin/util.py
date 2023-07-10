import typing

import ast
import pycardano
from frozendict import frozendict
from frozenlist2 import frozenlist

import uplc.ast as uplc


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
