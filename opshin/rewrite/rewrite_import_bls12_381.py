import ast
import typing
from _ast import ImportFrom, AST, Store, Assign, Name
from dataclasses import dataclass
from enum import Enum, auto

import uplc.ast

import pluthon as plt

from frozenlist2 import frozenlist

from ..typed_ast import *
from ..type_impls import (
    ClassType,
    InstanceType,
    ByteStringInstanceType,
    FunctionType,
    AtomicType,
    UnitType,
    IntegerType,
)
from ..util import CompilingNodeTransformer, force_params, OVar, OLambda

"""
Checks that there was an import of dataclass if there are any class definitions
"""


@dataclass(frozen=True, unsafe_hash=True)
class BLS12381G1ElementType(ClassType):
    def python_type(self):
        return "BLS12381G1Element"

    def constr_type(self):
        return InstanceType(
            FunctionType([BLS12381G1ElementInstance], BLS12381G1ElementInstance)
        )

    def constr(self) -> plt.AST:
        return OLambda(["x"], OVar("x"))

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        if isinstance(op, ast.Eq) and isinstance(o, BLS12381G1ElementType):
            return plt.BuiltIn(uplc.ast.BuiltInFun.Bls12_381_G1_Equal)
        raise NotImplementedError(
            f"Comparison {op.__class__.__name__} not implemented for {self.python_type()} and {o.python_type()}"
        )

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        if isinstance(other, InstanceType):
            other = other.typ
            if isinstance(other, BLS12381G1ElementType):
                if isinstance(binop, (ast.Add, ast.Sub)):
                    return BLS12381G1ElementType()
            if isinstance(other, IntegerType):
                if isinstance(binop, ast.Mult):
                    return BLS12381G1ElementType()
        return super()._binop_return_type(binop, other)

    def _binop_bin_fun(self, binop: ast.operator, other: "TypedAST"):
        if isinstance(other.typ, InstanceType):
            other = other.typ.typ
            if isinstance(other, BLS12381G1ElementType):
                if isinstance(binop, ast.Add):
                    return plt.Bls12_381_G1_Add
                if isinstance(binop, ast.Sub):
                    return lambda x, y: plt.Bls12_381_G1_Add(x, plt.Bls12_381_G1_Neg(y))
            if isinstance(other, IntegerType):
                if isinstance(binop, ast.Mult):
                    return lambda x, y: plt.Bls12_381_G1_ScalarMul(y, x)
        return super()._binop_bin_fun(binop, other)

    def attribute_type(self, attr) -> "Type":
        if attr == "compress":
            return InstanceType(FunctionType([], ByteStringInstanceType))
        return super().attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        if attr == "compress":
            return OLambda(["x", "_"], plt.Bls12_381_G1_Compress(OVar("x")))
        return super().attribute(attr)

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, (ast.USub, ast.UAdd)):
            return BLS12381G1ElementType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop):
        if isinstance(unop, ast.USub):
            return plt.Bls12_381_G1_Neg
        if isinstance(unop, ast.UAdd):
            return lambda x: x
        return super()._unop_fun(unop)

    def __ge__(self, other):
        return isinstance(other, BLS12381G1ElementType)


@dataclass(frozen=True, unsafe_hash=True)
class BLS12381G2ElementType(ClassType):
    def python_type(self):
        return "BLS12381G2Element"

    def constr_type(self):
        return InstanceType(
            FunctionType([BLS12381G2ElementInstance], BLS12381G2ElementInstance)
        )

    def constr(self) -> plt.AST:
        return OLambda(["x"], OVar("x"))

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        if isinstance(op, ast.Eq) and isinstance(o, BLS12381G2ElementType):
            return plt.BuiltIn(uplc.ast.BuiltInFun.Bls12_381_G2_Equal)
        raise NotImplementedError(
            f"Comparison {op.__class__.__name__} not implemented for {self.python_type()} and {o.python_type()}"
        )

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        if isinstance(other, InstanceType):
            other = other.typ
            if isinstance(other, BLS12381G2ElementType):
                if isinstance(binop, (ast.Add, ast.Sub)):
                    return BLS12381G2ElementType()
            if isinstance(other, IntegerType):
                if isinstance(binop, ast.Mult):
                    return BLS12381G2ElementType()
        return super()._binop_return_type(binop, other)

    def _binop_bin_fun(self, binop: ast.operator, other: "TypedAST"):
        if isinstance(other.typ, InstanceType):
            other = other.typ.typ
            if isinstance(other, BLS12381G2ElementType):
                if isinstance(binop, ast.Add):
                    return plt.Bls12_381_G2_Add
                if isinstance(binop, ast.Sub):
                    return lambda x, y: plt.Bls12_381_G2_Add(x, plt.Bls12_381_G2_Neg(y))
            if isinstance(other, IntegerType):
                if isinstance(binop, ast.Mult):
                    return lambda x, y: plt.Bls12_381_G2_ScalarMul(y, x)
        return super()._binop_bin_fun(binop, other)

    def attribute_type(self, attr) -> "Type":
        if attr == "compress":
            return InstanceType(FunctionType([], ByteStringInstanceType))
        return super().attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        if attr == "compress":
            return OLambda(["x", "_"], plt.Bls12_381_G2_Compress(OVar("x")))
        return super().attribute(attr)

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, (ast.USub, ast.UAdd)):
            return BLS12381G2ElementType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop):
        if isinstance(unop, ast.USub):
            return plt.Bls12_381_G2_Neg
        if isinstance(unop, ast.UAdd):
            return lambda x: x
        return super()._unop_fun(unop)

    def __ge__(self, other):
        return isinstance(other, BLS12381G2ElementType)


@dataclass(frozen=True, unsafe_hash=True)
class BLS12381MlresultType(ClassType):
    def python_type(self):
        return "BLS12381MillerLoopResult"

    def constr_type(self):
        return InstanceType(
            FunctionType([BLS12381MlresultInstance], BLS12381MlresultInstance)
        )

    def constr(self) -> plt.AST:
        return OLambda(["x"], OVar("x"))

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        if isinstance(other, InstanceType):
            other = other.typ
            if isinstance(other, BLS12381MlresultType):
                if isinstance(binop, ast.Mult):
                    return BLS12381MlresultType()
        return super()._binop_return_type(binop, other)

    def _binop_bin_fun(self, binop: ast.operator, other: "TypedAST"):
        if isinstance(other.typ, InstanceType):
            other = other.typ.typ
            if isinstance(other, BLS12381MlresultType):
                if isinstance(binop, ast.Mult):
                    return plt.Bls12_381_MulMlResult
        return super()._binop_bin_fun(binop, other)

    def __ge__(self, other):
        return isinstance(other, BLS12381MlresultType)


BLS12381G1ElementInstance = InstanceType(BLS12381G1ElementType())
BLS12381G2ElementInstance = InstanceType(BLS12381G2ElementType())
BLS12381MlresultInstance = InstanceType(BLS12381MlresultType())

BLS12_381_ENTRIES = {
    x.python_type(): x
    for x in (
        BLS12381G1ElementType(),
        BLS12381G2ElementType(),
        BLS12381MlresultType(),
    )
}


class RewriteImportBLS12381(CompilingNodeTransformer):
    step = "Resolving imports and usage of std.bls12_381"

    def visit_ImportFrom(self, node: ImportFrom) -> typing.Union[typing.List[AST], AST]:
        if node.module != "opshin.std.bls12_381":
            return node
        additional_assigns = []
        for n in node.names:
            imported_type = BLS12_381_ENTRIES.get(n.name)
            assert (
                imported_type is not None
            ), f"Unsupported type import from bls12_381 '{n.name}"
            imported_name = n.name if n.asname is None else n.asname
            additional_assigns.append(
                Assign(
                    targets=[Name(id=imported_name, ctx=Store())],
                    value=RawPlutoExpr(expr=plt.Unit(), typ=imported_type),
                )
            )
        return additional_assigns
