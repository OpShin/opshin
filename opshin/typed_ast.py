from .types import *

_LOGGER = logging.getLogger(__name__)


class TypedAST(AST):
    typ: Type


class typedexpr(TypedAST, expr):
    def typechecks(self) -> typing.Dict[str, Type]:
        """Successful typechecks if this expression evaluates to True"""
        return {}


class typedstmt(TypedAST, stmt):
    # Statements always have type None
    typ = NoneInstanceType


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


class TypedExpression(typedstmt, Expression):
    body: typedexpr


class TypedCall(typedexpr, Call):
    func: typedexpr
    args: typing.List[typedexpr]


class TypedExpr(typedstmt, Expr):
    value: typedexpr


class TypedAssign(typedstmt, Assign):
    targets: typing.List[typedexpr]
    value: typedexpr


class TypedClassDef(typedstmt, ClassDef):
    class_typ: Type


class TypedAnnAssign(typedstmt, AnnAssign):
    target: typedexpr
    annotation: Type
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
    pass


class TypedList(typedexpr, List):
    pass


class typedcomprehension(typedexpr, comprehension):
    target: typedexpr
    iter: typedexpr
    ifs: typing.List[typedexpr]


class TypedListComp(typedexpr, ListComp):
    generators: typing.List[typedcomprehension]
    elt: typedexpr


class TypedFormattedValue(typedexpr, FormattedValue):
    value: typedexpr
    conversion: int
    format_spec: typing.Optional[JoinedStr]


class TypedJoinedStr(typedexpr, JoinedStr):
    values: typing.List[typedexpr]


class TypedDict(typedexpr, Dict):
    pass


class TypedIfExp(typedstmt, IfExp):
    test: typedexpr
    body: typedexpr
    orelse: typedexpr


class TypedCompare(typedexpr, Compare):
    left: typedexpr
    ops: typing.List[cmpop]
    comparators: typing.List[typedexpr]


class TypedBinOp(typedexpr, BinOp):
    left: typedexpr
    right: typedexpr


class TypedBoolOp(typedexpr, BoolOp):
    values: typing.List[typedexpr]


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


class RawPlutoExpr(typedexpr):
    typ: Type
    expr: plt.AST
