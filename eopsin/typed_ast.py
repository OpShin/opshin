import ast

from ast import *
from dataclasses import dataclass
import typing


class Type:
    pass


@dataclass(unsafe_hash=True)
class InstanceType(Type):
    pass


@dataclass(unsafe_hash=True)
class RecordInstanceType(InstanceType):
    typ: str


@dataclass(unsafe_hash=True)
class UnionInstanceType(InstanceType):
    typs: typing.List[InstanceType]


@dataclass(unsafe_hash=True)
class OptionalInstanceType(InstanceType):
    typ: InstanceType


IntegerType = RecordInstanceType(int.__name__)
StringType = RecordInstanceType(str.__name__)
ByteStringType = RecordInstanceType(bytes.__name__)
BoolType = RecordInstanceType(bool.__name__)
UnitType = RecordInstanceType("Unit")


@dataclass(frozen=True, unsafe_hash=True)
class Record:
    name: str
    constructor: int
    fields: typing.List[typing.Tuple[str, Type]]


@dataclass(unsafe_hash=True)
class ClassType(Type):
    pass


@dataclass(unsafe_hash=True)
class RecordType(ClassType):
    record: Record


@dataclass(unsafe_hash=True)
class UnionType(ClassType):
    typs: typing.List[ClassType]


@dataclass(unsafe_hash=True)
class OptionalType(ClassType):
    typ: ClassType


NoneRecord = Record("None", 0, [])
NoneInstanceType = RecordInstanceType("None")
NoneType = RecordType(NoneRecord)


@dataclass(unsafe_hash=True)
class TupleType(Type):
    typs: typing.List[Type]


@dataclass(unsafe_hash=True)
class ListType(Type):
    typ: Type


@dataclass(unsafe_hash=True)
class DictType(Type):
    key_typ: Type
    value_typ: Type


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


class TypeInferenceError(AssertionError):
    pass


def type_from_annotation(ann: expr):
    if isinstance(ann, Constant):
        if ann.value is None:
            return NoneType
    if isinstance(ann, Tuple):
        if not ann.elts:
            # This is ()
            return UnitType
    if isinstance(ann, Name):
        return RecordInstanceType(ann.id)
    if isinstance(ann, Subscript):
        assert isinstance(
            ann.value, Name
        ), "Only Optional, Union, Dict and List are allowed as Generic types"
        assert isinstance(ann.slice, Index), "Generic types must be parameterized"
        if ann.value.id == "Optional":
            ann_type = type_from_annotation(ann.slice.value)
            assert isinstance(
                ann_type, InstanceType
            ), "Optional must have a single type as parameter"
            return OptionalInstanceType(ann_type)
        if ann.value.id == "Union":
            assert isinstance(
                ann.slice.value, Tuple
            ), "Union must combine multiple classes"
            ann_types = [type_from_annotation(e) for e in ann.slice.value.elts]
            assert all(
                isinstance(e, InstanceType) for e in ann_types
            ), "Union must combine multiple classes"
            return UnionInstanceType(ann_types)
        if ann.value.id == "List":
            return ListType(type_from_annotation(ann.slice.value))
        if ann.value.id == "Dict":
            assert isinstance(ann.slice.value, Tuple), "Dict must combine two classes"
            assert len(ann.slice.value.elts) == 2, "Dict must combine two classes"
            return DictType(
                type_from_annotation(ann.slice.value.elts[0]),
                type_from_annotation(ann.slice.value.elts[1]),
            )
        raise NotImplementedError(
            "Only Optional, Union, Dict and List are allowed as Generic types"
        )
    if ann is None:
        TypeInferenceError(
            "Type annotation is missing for a function argument or return value"
        )
    raise NotImplementedError(f"Annotation type {ann} is not supported")


class RecordReader(NodeVisitor):
    name: str
    constructor: int
    attributes: typing.List[typing.Tuple[str, Type]]

    def __init__(self):
        self.constructor = 0
        self.attributes = []

    @classmethod
    def extract(cls, c: ClassDef) -> Record:
        f = cls()
        f.visit(c)
        return Record(f.name, f.constructor, f.attributes)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        assert isinstance(
            node.target, Name
        ), "Record elements must have named attributes"
        if node.target.id != "CONSTR_ID":
            assert (
                node.value is None
            ), f"PlutusData attribute {node.target.id} may not have a default value"
            self.attributes.append(
                (node.target.id, type_from_annotation(node.annotation))
            )
            return
        assert isinstance(
            node.value, Constant
        ), "CONSTR_ID must be assigned a constant integer"
        assert isinstance(
            node.value.value, int
        ), "CONSTR_ID must be assigned an integer"
        self.constructor = node.value.value

    def visit_ClassDef(self, node: ClassDef) -> None:
        self.name = node.name
        for s in node.body:
            self.visit(s)

    def visit_Pass(self, node: Pass) -> None:
        pass

    def visit_Assign(self, node: Assign) -> None:
        assert len(node.targets) == 1, "Record elements must be assigned one by one"
        target = node.targets[0]
        assert isinstance(target, Name), "Record elements must have named attributes"
        assert (
            target.id == "CONSTR_ID"
        ), "Type annotations may only be omitted for CONSTRUCTOR"
        assert isinstance(
            node.value, Constant
        ), "CONSTR_ID must be assigned a constant integer"
        assert isinstance(
            node.value.value, int
        ), "CONSTR_ID must be assigned an integer"
        self.constructor = node.value.value

    def visit_Expr(self, node: Expr) -> None:
        assert isinstance(
            node.value, Constant
        ), "Only comments are allowed inside classes"
        return None

    def generic_visit(self, node: AST) -> None:
        raise NotImplementedError(f"Can not compile {node} inside of a class")
