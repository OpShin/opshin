import ast as _ast
import typing as _typing
import pluthon as _plt

from .type_impls import NoneInstanceType, Type


class TypedAST(_ast.AST):
    typ: "Type"


class typedexpr(TypedAST, _ast.expr):
    def typechecks(self) -> _typing.Dict[str, "Type"]:
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
    orig_name: str


class TypedIf(typedstmt, _ast.If):
    test: typedexpr
    body: _typing.List[typedstmt]
    orelse: _typing.List[typedstmt]


class TypedReturn(typedstmt, _ast.Return):
    value: typedexpr


class TypedExpression(typedstmt, _ast.Expression):
    body: typedexpr


class TypedCall(typedexpr, _ast.Call):
    func: typedexpr
    args: _typing.List[typedexpr]


class TypedExpr(typedstmt, _ast.Expr):
    value: typedexpr


class TypedAssign(typedstmt, _ast.Assign):
    targets: _typing.List[typedexpr]
    value: typedexpr


class TypedClassDef(typedstmt, _ast.ClassDef):
    class_typ: "Type"


class TypedAnnAssign(typedstmt, _ast.AnnAssign):
    target: typedexpr
    annotation: "Type"
    value: typedexpr


class TypedWhile(typedstmt, _ast.While):
    test: typedexpr
    body: _typing.List[typedstmt]
    orelse: _typing.List[typedstmt]


class TypedFor(typedstmt, _ast.For):
    target: typedexpr
    iter: typedexpr
    body: _typing.List[typedstmt]
    orelse: _typing.List[typedstmt]


class TypedPass(typedstmt, _ast.Pass):
    pass


class TypedName(typedexpr, _ast.Name):
    pass


class Typedkeyword(TypedAST, _ast.keyword):
    arg: typedexpr
    value: typedexpr


class TypedConstant(TypedAST, _ast.Constant):
    pass


class TypedTuple(typedexpr, _ast.Tuple):
    pass


class TypedList(typedexpr, _ast.List):
    pass


class typedcomprehension(typedexpr, _ast.comprehension):
    target: typedexpr
    iter: typedexpr
    ifs: _typing.List[typedexpr]


class TypedListComp(typedexpr, _ast.ListComp):
    elt: typedexpr
    generators: _typing.List[typedcomprehension]


class TypedDictComp(typedexpr, _ast.DictComp):
    key: typedexpr
    value: typedexpr
    generators: _typing.List[typedcomprehension]


class TypedFormattedValue(typedexpr, _ast.FormattedValue):
    value: typedexpr
    conversion: int
    format_spec: _typing.Optional[_ast.JoinedStr]


class TypedJoinedStr(typedexpr, _ast.JoinedStr):
    values: _typing.List[typedexpr]


class TypedDict(typedexpr, _ast.Dict):
    pass


class TypedIfExp(typedstmt, _ast.IfExp):
    test: typedexpr
    body: typedexpr
    orelse: typedexpr


class TypedCompare(typedexpr, _ast.Compare):
    left: typedexpr
    ops: _typing.List[_ast.cmpop]
    comparators: _typing.List[typedexpr]


class TypedBinOp(typedexpr, _ast.BinOp):
    left: typedexpr
    right: typedexpr


class TypedBoolOp(typedexpr, _ast.BoolOp):
    values: _typing.List[typedexpr]


class TypedUnaryOp(typedexpr, _ast.UnaryOp):
    operand: typedexpr


class TypedSubscript(typedexpr, _ast.Subscript):
    value: typedexpr


class TypedAttribute(typedexpr, _ast.Attribute):
    value: typedexpr
    pos: int


class TypedAssert(typedstmt, _ast.Assert):
    test: typedexpr
    msg: typedexpr


class TypedSlice(typedexpr, _ast.Slice):
    lower: _typing.Optional[typedexpr]
    upper: _typing.Optional[typedexpr]
    step: _typing.Optional[typedexpr]


class RawPlutoExpr(typedexpr):
    typ: "Type"
    expr: _plt.AST

    _attributes = ["lineno", "col_offset", "end_lineno", "end_col_offset"]
    _fields = []
