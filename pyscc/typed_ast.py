from ast import *
from dataclasses import dataclass
import typing


class Type:
    pass

@dataclass(unsafe_hash=True)
class InstanceType(Type):
    typ: str

IntegerType = InstanceType(int.__name__)
StringType = InstanceType(str.__name__)
ByteStringType = InstanceType(bytes.__name__)
BoolType = InstanceType(bool.__name__)
UnitType = InstanceType(type(None).__name__)
PlutusDataType = InstanceType("PlutusData")


@dataclass(frozen=True, unsafe_hash=True)
class Record:
    name: str
    attributes: typing.List[typing.Tuple[str, Type]]

@dataclass(unsafe_hash=True)
class ClassType(Type):
    record: Record

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
    typ = UnitType

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
            return UnitType
    if isinstance(ann, Name):
        return InstanceType(ann.id)
    if isinstance(ann, Subscript):
        raise NotImplementedError("Generic types not supported yet")
    if ann is None:
        TypeInferenceError("Type annotation is missing for a function argument or return value")
    raise NotImplementedError(f"Annotation type {ann} is not supported")

class RecordReader(NodeVisitor):
    name: str
    attributes: typing.List[typing.Tuple[str, Type]]

    def __init__(self):
        self.attributes = []

    @classmethod
    def extract(cls, c: ClassDef) -> Record:
        f = cls()
        f.visit(c)
        return Record(f.name, f.attributes)

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        assert isinstance(node.target, Name), "Record elements must have named attributes"
        self.attributes.append(
            (node.target.id, type_from_annotation(node.annotation))
        )

    def visit_ClassDef(self, node: ClassDef) -> None:
        self.name = node.name
        for s in node.body:
            self.visit(s)

    def generic_visit(self, node: AST) -> None:
        raise NotImplementedError(f"Can not compile {node} inside of a class")
