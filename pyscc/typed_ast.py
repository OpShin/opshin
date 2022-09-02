from ast import *
from dataclasses import dataclass
import typing

class Type:
    pass

@dataclass(unsafe_hash=True)
class InstanceType(Type):
    typ: str

@dataclass(unsafe_hash=True)
class ClassType(Type):
    typ: str

@dataclass(unsafe_hash=True)
class TupleType(Type):
    typs: typing.List[Type]

@dataclass(unsafe_hash=True)
class ListType(Type):
    typs: typing.List[Type]

@dataclass(unsafe_hash=True)
class FunctionType(Type):
    argtyps: typing.List[Type]
    rettyp: Type

class TypedAST(AST):
    typ: Type

class typedexpr(TypedAST, expr):
    pass

class typedstmt(TypedAST, stmt):
    # Statements always have type None
    typ = InstanceType(type(None).__name__)

class typedarg(TypedAST, arg):
    pass

class typedarguments(TypedAST, arguments):
    args: typing.List[typedarg]
    vararg: typing.Union[typedarg, None]
    kwonlyargs: typing.List[typedarg]
    kw_defaults: typing.List[typing.Union[typedexpr,None]]
    kwarg: typing.Union[typedarg, None]
    defaults: typing.List[typedexpr]

class TypedModule(typedstmt, Module):
    body: typing.List[typedstmt]

class TypedFunctionDef(typedstmt, FunctionDef):
    body: typing.List[typedstmt]
    args: arguments

class TypedIf(typedstmt, If):
    cond: typedexpr
    body: typing.List[typedstmt]
    orelse: typing.List[typedstmt]

class TypedReturn(typedstmt, Return):
    value: typedexpr

class TypedExpression(typedexpr, Expression):
    body: typedexpr

class TypedCall(typedexpr, Call):
    func: typedexpr
    args: typing.List[typedexpr]

class TypedExpr(typedstmt, Expr):
    value: typedexpr


class TypedAssign(typedstmt, Assign):
    targets: typing.List[typedexpr]
    value: typedexpr

class TypedPass(typedstmt, Pass):
    pass

class TypedName(typedexpr, Name):
    pass

class TypedConstant(TypedAST, Constant):
    pass


class TypedTuple(typedexpr, Tuple):
    typ: typing.List[TypedAST]

class TypedList(typedexpr, List):
    typ: typing.List[TypedAST]

class TypedCompare(typedexpr, Compare):
    left: typedexpr
    ops: typing.List[cmpop]
    comparators: typing.List[typedexpr]

class TypedBinOp(typedexpr, BinOp):
    left: typedexpr
    right: typedexpr

class TypedUnaryOp(typedexpr, UnaryOp):
    operand: typedexpr