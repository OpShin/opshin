import ast
from frozenlist import FrozenList

from ast import *
from dataclasses import dataclass
import typing


def FrozenFrozenList(l: list):
    fl = FrozenList(l)
    fl.freeze()
    return fl


class Type:
    pass


@dataclass(frozen=True, unsafe_hash=True)
class Record:
    name: str
    constructor: int
    fields: typing.Union[typing.List[typing.Tuple[str, Type]], FrozenList]


@dataclass(frozen=True, unsafe_hash=True)
class ClassType(Type):
    pass


@dataclass(frozen=True, unsafe_hash=True)
class AtomicType(ClassType):
    typ: str


@dataclass(frozen=True, unsafe_hash=True)
class RecordType(ClassType):
    record: Record


@dataclass(frozen=True, unsafe_hash=True)
class UnionType(ClassType):
    typs: typing.List[ClassType]


@dataclass(frozen=True, unsafe_hash=True)
class OptionalType(ClassType):
    typ: ClassType


@dataclass(frozen=True, unsafe_hash=True)
class TupleType(ClassType):
    typs: typing.List[Type]


@dataclass(frozen=True, unsafe_hash=True)
class ListType(ClassType):
    typ: Type


@dataclass(frozen=True, unsafe_hash=True)
class DictType(ClassType):
    key_typ: Type
    value_typ: Type


@dataclass(frozen=True, unsafe_hash=True)
class FunctionType(ClassType):
    argtyps: typing.List[Type]
    rettyp: Type


@dataclass(frozen=True, unsafe_hash=True)
class InstanceType(Type):
    typ: ClassType


@dataclass(frozen=True, unsafe_hash=True)
class OptionalInstanceType(InstanceType):
    typ: OptionalType


IntegerType = AtomicType(int.__name__)
StringType = AtomicType(str.__name__)
ByteStringType = AtomicType(bytes.__name__)
BoolType = AtomicType(bool.__name__)
UnitType = AtomicType("Unit")
IntegerInstanceType = InstanceType(IntegerType)
StringInstanceType = InstanceType(StringType)
ByteStringInstanceType = InstanceType(ByteStringType)
BoolInstanceType = InstanceType(BoolType)
UnitInstanceType = InstanceType(UnitType)

ATOMIC_TYPES = [
    IntegerType.typ,
    StringType.typ,
    ByteStringType.typ,
    BoolType.typ,
    UnitType.typ,
]


NoneRecord = Record("None", 0, FrozenFrozenList([]))
NoneType = RecordType(NoneRecord)
NoneInstanceType = InstanceType(NoneType)


class TypedAST(AST):
    typ: Type


class typedexpr(TypedAST, expr):
    pass


class typedstmt(TypedAST, stmt):
    # Statements always have type None
    typ = NoneType


class typedarg(TypedAST, arg):
    pass


class typedarguments(TypedAST, arguments):
    args: typing.List[typedarg]
    vararg: typing.Union[typedarg, None]
    kwonlyargs: typing.List[typedarg]
    kw_defaults: typing.List[typing.Union[typedexpr, None]]
    kwarg: typing.Union[typedarg, None]
    defaults: typing.List[typedexpr]


class TypedModule(typedstmt, Module):
    body: typing.List[typedstmt]


class TypedFunctionDef(typedstmt, FunctionDef):
    body: typing.List[typedstmt]
    args: arguments


class TypedIf(typedstmt, If):
    test: typedexpr
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


class TypedWhile(typedstmt, While):
    test: typedexpr
    body: typing.List[typedstmt]
    orelse: typing.List[typedstmt]


class TypedFor(typedstmt, For):
    target: typedexpr
    iter: typedexpr
    body: typing.List[typedstmt]
    orelse: typing.List[typedstmt]


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


class TypedSubscript(typedexpr, Subscript):
    value: typedexpr


class TypedAttribute(typedexpr, Attribute):
    value: typedexpr
    pos: int


class TypedAssert(typedstmt, Assert):
    test: typedexpr
    msg: typedexpr


class TypeInferenceError(AssertionError):
    pass
