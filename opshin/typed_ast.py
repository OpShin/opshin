import ast as _ast
import typing as _typing
import pluthon as _plt

from .type_impls import Type, NoneInstanceType


class TypedAST(_ast.AST):
    typ: Type


class typedexpr(TypedAST, _ast.expr):
    def typechecks(self) -> _typing.Dict[str, Type]:
        """Successful typechecks if this expression evaluates to True"""
        return {}


class typedstmt(TypedAST, _ast.stmt):
    # Statements always have type None
    typ = NoneInstanceType


class typedarg(TypedAST, _ast.arg):
    pass


class typedarguments(TypedAST, _ast.arguments):
    args: _typing.List[typedarg]
    vararg: _typing.Union[typedarg, None]
    kwonlyargs: _typing.List[typedarg]
    kw_defaults: _typing.List[_typing.Union[typedexpr, None]]
    kwarg: _typing.Union[typedarg, None]
    defaults: _typing.List[typedexpr]


class TypedModule(typedstmt, _ast.Module):
    body: _typing.List[typedstmt]


class TypedFunctionDef(typedstmt, _ast.FunctionDef):
    body: _typing.List[typedstmt]
    args: typedarguments


class TypedIf(typedstmt, _ast.If):
    test: typedexpr
    body: _typing.List[typedstmt]
    orelse: _typing.List[typedstmt]


class TypedReturn(typedstmt, Return):
    value: typedexpr


class TypedExpression(typedstmt, Expression):
    body: typedexpr


class TypedCall(typedexpr, Call):
    func: typedexpr
    args: _typing.List[typedexpr]


class TypedExpr(typedstmt, Expr):
    value: typedexpr


class TypedAssign(typedstmt, Assign):
    targets: _typing.List[typedexpr]
    value: typedexpr


class TypedClassDef(typedstmt, ClassDef):
    class_typ: Type


class TypedAnnAssign(typedstmt, AnnAssign):
    target: typedexpr
    annotation: Type
    value: typedexpr


class TypedWhile(typedstmt, While):
    test: typedexpr
    body: _typing.List[typedstmt]
    orelse: _typing.List[typedstmt]


class TypedFor(typedstmt, For):
    target: typedexpr
    iter: typedexpr
    body: _typing.List[typedstmt]
    orelse: _typing.List[typedstmt]


class TypedPass(typedstmt, Pass):
    pass


class TypedName(typedexpr, Name):
    pass


class Typedkeyword(TypedAST, keyword):
    arg: typedexpr
    value: typedexpr


class TypedConstant(TypedAST, Constant):
    pass


class TypedTuple(typedexpr, Tuple):
    pass


class TypedList(typedexpr, List):
    pass


class typedcomprehension(typedexpr, comprehension):
    target: typedexpr
    iter: typedexpr
    ifs: _typing.List[typedexpr]


class TypedListComp(typedexpr, ListComp):
    elt: typedexpr
    generators: _typing.List[typedcomprehension]


class TypedDictComp(typedexpr, DictComp):
    key: typedexpr
    value: typedexpr
    generators: _typing.List[typedcomprehension]


class TypedFormattedValue(typedexpr, FormattedValue):
    value: typedexpr
    conversion: int
    format_spec: _typing.Optional[JoinedStr]


class TypedJoinedStr(typedexpr, JoinedStr):
    values: _typing.List[typedexpr]


class TypedDict(typedexpr, Dict):
    pass


class TypedIfExp(typedstmt, IfExp):
    test: typedexpr
    body: typedexpr
    orelse: typedexpr


class TypedCompare(typedexpr, Compare):
    left: typedexpr
    ops: _typing.List[cmpop]
    comparators: _typing.List[typedexpr]


class TypedBinOp(typedexpr, BinOp):
    left: typedexpr
    right: typedexpr


class TypedBoolOp(typedexpr, BoolOp):
    values: _typing.List[typedexpr]


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
    expr: _plt.AST

    _attributes = ["lineno", "col_offset", "end_lineno", "end_col_offset"]
    _fields = []
