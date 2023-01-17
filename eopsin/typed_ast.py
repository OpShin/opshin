import typing
from ast import *
from dataclasses import dataclass

from frozenlist import FrozenList

import pluthon as plt
from eopsin import empty_list


def FrozenFrozenList(l: list):
    fl = FrozenList(l)
    fl.freeze()
    return fl


class Type:
    def constr_type(self) -> FunctionType:
        """The type of the constructor for this class"""
        raise TypeInferenceError(f"Object of type {self} does not have a constructor")

    def constr(self) -> plt.AST:
        """The constructor for this class"""
        raise NotImplementedError(f"Constructor of {self} not implemented")

    def attribute_type(self, attr) -> "Type":
        """The types of the named attributes of this class"""
        raise TypeInferenceError(
            f"Object of type {self} does not have attribute {attr}"
        )

    def attribute(self, attr) -> plt.AST:
        """The attributes of this class. Needs to be a lambda that expects as first argument the object itself"""
        raise NotImplementedError(f"Attribute {attr} not implemented for type {self}")


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

    def constr_type(self) -> FunctionType:
        return FunctionType(self.record.fields, InstanceType(self))

    def constr(self) -> plt.AST:
        # wrap all constructor values to PlutusData
        build_constr_params = plt.EmptyDataList()
        for n, t in reversed(self.record.fields):
            build_constr_params = plt.MkCons(
                transform_output_map(t)(plt.Var(n)), build_constr_params
            )
        # then build a constr type with this PlutusData
        return plt.Lambda(
            [n for n, _ in self.record.fields] + ["_"],
            plt.ConstrData(
                plt.Integer(self.record.constructor), plt.ListData(build_constr_params)
            ),
        )

    def attribute_type(self, attr: str) -> Type:
        """The types of the named attributes of this class"""
        if attr == "CONSTR_ID":
            return InstanceType(IntegerType)
        for n, t in self.record.fields:
            if n == attr:
                return t
        raise TypeInferenceError(f"Type {self} does not have attribute {attr}")

    def attribute(self, attr: str) -> plt.AST:
        """The attributes of this class. Need to be a lambda that expects as first argument the object itself and as last argument the statemonad"""
        if attr == "CONSTR_ID":
            # access to constructor
            return plt.Lambda(
                ["self", "_"],
                plt.Constructor(plt.Var("self")),
            )
        attr_typ = self.attribute_type(attr)
        pos = next(i for i, (n, _) in enumerate(self.record.fields) if n == attr)
        # access to normal fields
        return plt.Lambda(
            ["self", "_"],
            transform_ext_params_map(attr_typ)(
                plt.NthField(
                    plt.Var("self"),
                    plt.Integer(pos),
                ),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class UnionType(ClassType):
    typs: typing.List[ClassType]


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

    def constr_type(self) -> FunctionType:
        raise TypeInferenceError(f"Can not construct an instance {self}")

    def constr(self) -> plt.AST:
        raise NotImplementedError(f"Can not construct an instance {self}")

    def attribute_type(self, attr) -> Type:
        return self.typ.attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        return self.typ.attribute(attr)


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


TransformExtParamsMap = {
    IntegerInstanceType: lambda x: plt.UnIData(x),
    ByteStringInstanceType: lambda x: plt.UnBData(x),
    StringInstanceType: lambda x: plt.DecodeUtf8(plt.UnBData(x)),
    UnitInstanceType: lambda x: plt.Lambda(["_"], plt.Unit()),
    BoolInstanceType: lambda x: plt.NotEqualsInteger(x, plt.Integer(0)),
}


def transform_ext_params_map(p: Type):
    assert isinstance(
        p, InstanceType
    ), "Can only transform instances, not classes as input"
    if p in TransformExtParamsMap:
        return TransformExtParamsMap[p]
    if isinstance(p.typ, ListType):
        list_int_typ = p.typ.typ
        return lambda x: plt.MapList(
            plt.UnListData(x),
            plt.Lambda(["x"], transform_ext_params_map(list_int_typ)(plt.Var("x"))),
            empty_list(p.typ.typ),
        )
    if isinstance(p.typ, DictType):
        # TODO also remap in the style the list is mapped (but on pairs)
        raise NotImplementedError(
            "Dictionaries can currently not be parsed from PlutusData"
        )
    return lambda x: x


TransformOutputMap = {
    StringInstanceType: lambda x: plt.BData(plt.EncodeUtf8(x)),
    IntegerInstanceType: lambda x: plt.IData(x),
    ByteStringInstanceType: lambda x: plt.BData(x),
    UnitInstanceType: lambda x: plt.Lambda(["_"], plt.Unit()),
    BoolInstanceType: lambda x: plt.IData(
        plt.IfThenElse(x, plt.Integer(1), plt.Integer(0))
    ),
}


def transform_output_map(p: Type):
    assert isinstance(
        p, InstanceType
    ), "Can only transform instances, not classes as input"
    if p in TransformOutputMap:
        return TransformOutputMap[p]
    if isinstance(p.typ, ListType):
        list_int_typ = p.typ.typ
        return lambda x: plt.ListData(
            plt.MapList(
                x,
                plt.Lambda(["x"], transform_output_map(list_int_typ)(plt.Var("x"))),
            ),
        )
    if isinstance(p.typ, DictType):
        # TODO also remap in the style the list is mapped as input
        raise NotImplementedError(
            "Dictionaries can currently not be mapped to PlutusData"
        )
    return lambda x: x
