from enum import Enum

from .type_inference import *
from . import pluto_ast as plt, uplc_ast
from .rewrite_for import RewriteFor
from .rewrite_tuple_assign import RewriteTupleAssign
from .rewrite_augassign import RewriteAugAssign
from .rewrite_dataclass import RewriteDataclasses
from .uplc_ast import BuiltInFun

STATEMONAD = "s"


class ReturnTupleElem(Enum):
    STATE_FLAG = 0
    STATE_MONAD = 1
    RETURN_VALUE = 2


RETURN_TUPLE_SIZE = len(ReturnTupleElem)


class StateFlags(Enum):
    CONTINUE = 0
    ABORT = 1
    RETURN = 2


ConstantMap = {
    str: plt.Text,
    bytes: plt.ByteString,
    int: lambda s, x: from_primitive_int(s, plt.Integer(x)),
    bool: lambda s, x: from_primitive_bool(s, plt.Bool(x)),
    # TODO support higher level Optional type
    type(None): lambda s, x: from_primitive_none(s),
}


def extend_statemonad(
    names: typing.List[str],
    values: typing.List[plt.AST],
    old_statemonad: plt.MutableMap,
):
    return plt.extend_map([n.encode() for n in names], values, old_statemonad)


INTEGER_ATTRIBUTE_VARNAME = b"\0int_attribute"
BOOL_ATTRIBUTE_VARNAME = b"\0bool_attribute"
NONE_ATTRIBUTE_VARNAME = b"\0None_attribute"
TYPE_ATTRIBUTE_VARNAME = b"\0type_attribute"

to_primitive_int = plt.to_primitive
to_primitive_bool = plt.to_primitive


def from_primitive_int(statemonad: plt.AST, p: plt.AST):
    return plt.from_primitive(
        p, plt.Apply(statemonad, INTEGER_ATTRIBUTE_VARNAME)
    )


def from_primitive_bool(statemonad: plt.AST, p: plt.AST):
    return plt.from_primitive(p, plt.Apply(statemonad, BOOL_ATTRIBUTE_VARNAME))

def from_primitive_none(statemonad: plt.AST):
    return plt.Apply(statemonad, NONE_ATTRIBUTE_VARNAME)

def state_flag(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.STATE_FLAG.value, RETURN_TUPLE_SIZE)


def state_monad(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.STATE_MONAD.value, RETURN_TUPLE_SIZE)


def return_value(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.RETURN_VALUE.value, RETURN_TUPLE_SIZE)


def exception(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.RETURN_VALUE.value, RETURN_TUPLE_SIZE)


def exception_isset(ret: plt.AST):
    return plt.EqualsInteger(state_flag(ret), plt.Integer(StateFlags.ABORT.value))


def normal_return(state_monad: plt.AST, return_value: plt.AST):
    return plt.Tuple(
        plt.Integer(StateFlags.RETURN.value),
        state_monad,
        return_value,
    )


def except_return(state_monad: plt.AST, exception: plt.AST):
    return plt.Tuple(
        plt.Integer(StateFlags.ABORT.value),
        state_monad,
        exception,
    )


def MethodCall(wv: plt.WrappedValue, statemonad: plt.AST, method_name: str, *args: plt.AST):
    return plt.Apply(
        plt.Apply(
            wv,
            method_name.encode(),
            plt.Lambda(
                [STATEMONAD, "self", [str(i) for i, _ in enumerate(args)]],
                # TODO exceptions could also be a bit more fancy wrapped objects
                except_return(plt.Var("self"), plt.Text("AttributeError")),
            ),
        ),
        statemonad,
        wv,
        *args,
    )


def AttributeAccess(wv: plt.WrappedValue, statemonad: plt.Var, attribute_name: str):
    return MethodCall(wv, statemonad, attribute_name)


def chain_except(a: plt.AST, b: plt.AST, c: plt.AST):
    """
    The monad combinator
    b/c must expect statemonad and return value of a as first two arguments
    """
    return plt.Apply(
        plt.Lambda(
            ["r"],
            plt.Ite(
                exception_isset(plt.Var("r")),
                plt.Apply(c, state_monad(plt.Var("r")), return_value(plt.Var("r"))),
                plt.Apply(b, state_monad(plt.Var("r")), return_value(plt.Var("r"))),
            ),
        ),
        a,
    )


def chain(a: plt.AST, b: plt.AST):
    # clean but inefficient implementation
    return chain_except(
        a,
        b,
        plt.Lambda([STATEMONAD, "e"], except_return(plt.Var(STATEMONAD), plt.Var("e"))),
    )


def try_catch(t: plt.AST, c: plt.AST):
    """
    Try evaluating code t.
    If t raises an exception, compare to e, if matches, evaluate c, otherwise pass on return value.
    c has to expect the raised exception as second parameter (after the state monad)
    Expects the statemonad as first argument
    """
    # clean but inefficient implementation
    return chain_except(
        t,
        plt.Lambda([STATEMONAD, "r"], normal_return(plt.Var(STATEMONAD), plt.Var("r"))),
        c,
    )
    # unclean but efficient implementation
    # plt.Lambda(
    #     [STATEMONAD],
    #     plt.Let(
    #         [("res", plt.Apply(t, plt.Var(STATEMONAD)))],
    #         plt.Ite(
    #             exception_isset(plt.Var("res")),
    #             plt.Apply(c, plt.Var(STATEMONAD), exception(plt.Var("res"))),
    #             plt.Var("res"),
    #         ),
    #     ),
    # )


# self is the simplest source of non-infinitely recursing, complete, integer attributes
INTEGER_ATTRIBUTES_MAP = {
    "__add__": Lambda(
        [STATEMONAD, "self", "other"],
        chain(
            MethodCall(plt.Var("other"), plt.Var(STATEMONAD), "__int__"),
            plt.Lambda(
                [STATEMONAD, "other_int"],
                normal_return(
                    plt.Var(STATEMONAD),
                    from_primitive_int(
                        plt.Var(STATEMONAD),
                        plt.AddInteger(
                            to_primitive_int(plt.Var("self")),
                            to_primitive_int(plt.Var("other_int")),
                        )
                    ),
                ),
            ),
        ),
    ),
    "__sub__": Lambda(
        [STATEMONAD, "self", "other"],
        chain(
            MethodCall(plt.Var("other"), plt.Var(STATEMONAD), "__int__"),
            plt.Lambda(
                [STATEMONAD, "other_int"],
                normal_return(
                    plt.Var(STATEMONAD),
                    from_primitive_int(
                        plt.Var(STATEMONAD),
                        plt.SubtractInteger(
                            to_primitive_int(plt.Var("self")),
                            to_primitive_int(plt.Var("other_int")),
                        )
                    ),
                ),
            ),
        ),
    ),
    "__eq__": Lambda(
        [STATEMONAD, "self", "other"],
        chain_except(
            plt.MethodCall(plt.Var("other"), plt.Var(STATEMONAD), "__int__"),
            plt.Lambda(
                [STATEMONAD, "other_int"],
                normal_return(
                    plt.Var(STATEMONAD),
                    from_primitive_bool(
                        plt.Var(STATEMONAD),
                        plt.EqualsInteger(
                            to_primitive_int(plt.Var("self")),
                            to_primitive_int(plt.Var("other_int")),
                        )
                    ),
                ),
            ),
            plt.Lambda(
                [STATEMONAD, "other_int"],
                normal_return(
                    plt.Var(STATEMONAD), from_primitive_bool(plt.Var(STATEMONAD), plt.Bool(False))
                ),
            ),
        ),
    ),
    "__int__": Lambda(
        [STATEMONAD, "self"],
        normal_return(plt.Var(STATEMONAD), plt.Var("self")),
    ),
    "__bool__": Lambda(
        [STATEMONAD, "self"],
        normal_return(
            plt.Var(STATEMONAD),
            from_primitive_bool(
                plt.Var(STATEMONAD),
                plt.NotEqualsInteger(to_primitive_int(plt.Var("self")), plt.Integer(0))
            ),
        ),
    ),
}

INTEGER_ATTRIBUTES = plt.extend_map(
    [k.encode() for k in INTEGER_ATTRIBUTES_MAP.keys()],
    INTEGER_ATTRIBUTES_MAP.values(),
    plt.MutableMap(),
)

BOOL_ATTRIBUTES_MAP = {
    "__add__": Lambda(
        [STATEMONAD, "self", "other"],
        chain(
            MethodCall(plt.Var("other"), plt.Var(STATEMONAD), "__int__"),
            plt.Lambda(
                [STATEMONAD, "other_int"],
                normal_return(
                    plt.Var(STATEMONAD),
                    from_primitive_int(
                        plt.Var(STATEMONAD),
                        plt.AddInteger(
                            # shortcut because we know there wont be an exception here
                            to_primitive_int(
                                return_value(
                                    MethodCall(
                                        plt.Var("self"), plt.Var(STATEMONAD), "__int__"
                                    )
                                )
                            ),
                            to_primitive_int(plt.Var("other_int")),
                        )
                    ),
                ),
            ),
        ),
    ),
    "__sub__": Lambda(
        [STATEMONAD, "self", "other"],
        chain(
            MethodCall(plt.Var("other"), plt.Var(STATEMONAD), "__int__"),
            plt.Lambda(
                [STATEMONAD, "other_int"],
                normal_return(
                    plt.Var(STATEMONAD),
                    from_primitive_int(
                        plt.Var(STATEMONAD),
                        plt.SubtractInteger(
                            # shortcut because we know there wont be an exception here
                            to_primitive_int(
                                return_value(
                                    MethodCall(
                                        plt.Var("self"), plt.Var(STATEMONAD), "__int__"
                                    )
                                )
                            ),
                            to_primitive_int(plt.Var("other_int")),
                        )
                    ),
                ),
            ),
        ),
    ),
    "__eq__": Lambda(
        [STATEMONAD, "self", "other"],
        chain_except(
            plt.MethodCall(plt.Var("other"), plt.Var(STATEMONAD), "__bool__"),
            plt.Lambda(
                [STATEMONAD, "other_bool"],
                normal_return(
                    plt.Var(STATEMONAD),
                    from_primitive_bool(
                        plt.Var(STATEMONAD),
                        plt.EqualsBool(
                            to_primitive_bool(plt.Var("self")),
                            to_primitive_bool(plt.Var("other_bool")),
                        )
                    ),
                ),
            ),
            plt.Lambda(
                [STATEMONAD, "other_bool"],
                normal_return(
                    plt.Var(STATEMONAD), from_primitive_bool(plt.Var(STATEMONAD), plt.Bool(False))
                ),
            ),
        ),
    ),
    "__int__": Lambda(
        [STATEMONAD, "self"],
        normal_return(
            plt.Var(STATEMONAD),
            from_primitive_int(
                plt.Var(STATEMONAD),
                plt.Ite(
                    to_primitive_bool(plt.Var("self")), plt.Integer(1), plt.Integer(0)
                )
            ),
        ),
    ),
    "__bool__": Lambda(
        [STATEMONAD, "self"],
        normal_return(plt.Var(STATEMONAD), plt.Var("self")),
    ),
}

BOOL_ATTRIBUTES = plt.extend_map(
    [k.encode() for k in BOOL_ATTRIBUTES_MAP.keys()],
    BOOL_ATTRIBUTES_MAP.values(),
    plt.MutableMap(),
)

NONE_CLASS = b"NoneType"

NONE_ATTRIBUTES_MAP = {
    # TODO properly define __eq__
    "__bool__": Lambda(
        [STATEMONAD, "self"],
        normal_return(plt.Var(STATEMONAD), from_primitive_bool(plt.Var(STATEMONAD), plt.Bool(False))),
    ),
}

NONE_ATTRIBUTES = plt.extend_map(
    [k.encode() for k in NONE_ATTRIBUTES_MAP.keys()],
    NONE_ATTRIBUTES_MAP.values(),
    plt.MutableMap(),
)

INITIAL_ATTRIBUTES = {
    INTEGER_ATTRIBUTE_VARNAME: INTEGER_ATTRIBUTES,
    BOOL_ATTRIBUTE_VARNAME: BOOL_ATTRIBUTES,
    NONE_ATTRIBUTE_VARNAME: NONE_ATTRIBUTES,
}

INITIAL_STATE = plt.extend_map(
    INITIAL_ATTRIBUTES.keys(),
    INITIAL_ATTRIBUTES.values(),
    plt.MutableMap,
)


PYTHON_BUILT_INS = {
    "None": plt.Lambda(
        [STATEMONAD],
        normal_return(
            plt.Var(STATEMONAD), plt.Apply(plt.Var(STATEMONAD), NONE_ATTRIBUTE_VARNAME)
        ),
    ),
    "print": plt.Lambda(
        [STATEMONAD, "x"],
        normal_return(
            plt.Var(STATEMONAD),
            plt.Apply(
                plt.Lambda(["a", "b"], plt.Var("b")),
                plt.Trace(
                    # TODO call str(x)
                    plt.Var("x"),
                    plt.Unit(),
                ),
                plt.Apply(plt.Var(STATEMONAD), NONE_ATTRIBUTE_VARNAME)
            )
        ),
    ),
    "int": plt.Lambda(
        [STATEMONAD, "x"],
        # TODO fall back to trying to parse str -> int
        MethodCall(plt.Var("x"), plt.Var(STATEMONAD), "__int__"),
    ),
}


INITIAL_STATE = extend_statemonad(
    PYTHON_BUILT_INS.keys(),
    PYTHON_BUILT_INS.values(),
    INITIAL_STATE,
)


BinOpMap = {
    Add: "__add__",
    Sub: "__sub__",
    Mult: "__mul__",
}

CmpMap = {
    Eq: "__eq__",
    NotEq: "__neq__",
    LtE: "__lte__",
    Lt: "__lt__",
    Gt: "__gt__",
    GtE: "__gte__",
}


class UPLCCompiler(NodeTransformer):
    """
    Expects a TypedAST and returns UPLC/Pluto like code
    """

    def visit(self, node):
        """Visit a node."""
        node_class_name = node.__class__.__name__
        if node_class_name.startswith("Typed"):
            node_class_name = node_class_name[len("Typed") :]
        method = "visit_" + node_class_name
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def visit_sequence(self, node_seq: typing.List[typedstmt]) -> plt.AST:
        s = plt.Var(STATEMONAD)
        for n in node_seq:
            compiled_stmt = self.visit(n)
            # TODO also abort with return
            s = plt.Apply(
                plt.Lambda(
                    ["r"],
                    plt.Ite(
                        plt.EqualsInteger(state_flag(plt.Var("r")), plt.Integer(StateFlags.CONTINUE.value)),
                        plt.Apply(compiled_stmt, state_monad(plt.Var("r"))),
                        # Either it is abort or return - in both cases, just return whatever that step returned
                        plt.Var("r"),
                    ),
                ),
                s,
            )
        return plt.Lambda([STATEMONAD], s)

    def visit_BinOp(self, node: TypedBinOp) -> plt.AST:
        opmet = BinOpMap.get(type(node.op))
        if opmet is None:
            raise NotImplementedError(f"Operation {node.op} is not implemented")
        return plt.Lambda(
            [STATEMONAD],
            MethodCall(self.visit(node.left), plt.Var(STATEMONAD), opmet, plt.Apply(self.visit(node.right), plt.Var(STATEMONAD))),
        )

    def visit_Compare(self, node: Compare) -> plt.AST:
        assert len(node.ops) == 1, "Only single comparisons are supported"
        assert len(node.comparators) == 1, "Only single comparisons are supported"
        opmet = CmpMap.get(type(node.ops[0]))
        if opmet is None:
            raise NotImplementedError(f"Operation {node.ops[0]} is not implemented")
        return plt.Lambda(
            [STATEMONAD],
            MethodCall(self.visit(node.left), plt.Var(STATEMONAD), opmet, plt.Apply(self.visit(node.comparators[0]), plt.Var(STATEMONAD))),
        )

    def visit_Module(self, node: TypedModule) -> plt.AST:
        cp = plt.Program(
            "0.0.1",
            try_catch(
                plt.Let(
                    [
                        (
                            "g",
                            plt.Apply(
                                plt.Apply(self.visit_sequence(node.body), INITIAL_STATE),
                                plt.ByteString("validator".encode("utf8")),
                            ),
                        )
                    ],
                    plt.Apply(plt.Var("g"), plt.Var("g")),
                ),
                plt.Lambda(
                    [STATEMONAD, "e"],
                    plt.Trace(
                        plt.Var("e"),
                        plt.Error(),
                    )
                )

            )
        )
        return cp

    def visit_Constant(self, node: TypedConstant) -> plt.AST:
        plt_type = ConstantMap.get(type(node.value))
        if plt_type is None:
            raise NotImplementedError(
                f"Constants of type {type(node.value)} are not supported"
            )
        return plt.Lambda([STATEMONAD], plt_type(node.value))

    def visit_NoneType(self, _: typing.Optional[typing.Any]) -> plt.AST:
        return plt.Lambda([STATEMONAD], from_primitive_none(plt.Var(STATEMONAD)))

    def visit_Assign(self, node: TypedAssign) -> plt.AST:
        assert (
            len(node.targets) == 1
        ), "Assignments to more than one variable not supported yet"
        assert isinstance(
            node.targets[0], Name
        ), "Assignments to other things then names are not supported"
        compiled_e = self.visit(node.value)
        # (\{STATEMONAD} -> (\x -> if (x ==b {self.visit(node.targets[0])}) then ({compiled_e} {STATEMONAD}) else ({STATEMONAD} x)))
        return plt.Lambda(
            [STATEMONAD],
            extend_statemonad(
                [node.targets[0].id],
                [plt.Apply(compiled_e, plt.Var(STATEMONAD))],
                plt.Var(STATEMONAD),
            ),
        )

    def visit_Name(self, node: TypedName) -> plt.AST:
        # depending on load or store context, return the value of the variable or its name
        if isinstance(node.ctx, Load):
            return plt.Lambda(
                [STATEMONAD],
                plt.Apply(plt.Var(STATEMONAD), plt.ByteString(node.id.encode())),
            )
        raise NotImplementedError(f"Context {node.ctx} not supported")

    def visit_Expr(self, node: TypedExpr) -> plt.AST:
        # we exploit UPLCs eager evaluation here
        # the expression is computed even though its value is eventually discarded
        # Note this really only makes sense for Trace
        return plt.Lambda(
            [STATEMONAD],
            plt.Apply(
                plt.Lambda(["_"], plt.Var(STATEMONAD)),
                plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
            ),
        )

    def visit_Call(self, node: TypedCall) -> plt.AST:
        # compiled_args = " ".join(f"({self.visit(a)} {STATEMONAD})" for a in node.args)
        # return rf"(\{STATEMONAD} -> ({self.visit(node.func)} {compiled_args})"
        return plt.Lambda(
            [STATEMONAD],
            plt.Let(
                [("g", plt.Apply(self.visit(node.func), plt.Var(STATEMONAD)))],
                plt.Apply(
                    plt.Var("g"),
                    # pass the function to itself for recursion
                    plt.Var("g"),
                    *(plt.Apply(self.visit(a), plt.Var(STATEMONAD)) for a in node.args),
                ),
            ),
        )

    def visit_FunctionDef(self, node: TypedFunctionDef) -> plt.AST:
        body = node.body.copy()
        if not isinstance(body[-1], Return):
            tr = Return(None)
            tr.typ = UnitType
            assert (
                node.typ.rettyp == UnitType
            ), "Function has no return statement but is supposed to return not-None value"
            body.append(tr)
        compiled_body = self.visit_sequence(body[:-1])
        compiled_return = self.visit(body[-1].value)
        args_state = extend_statemonad(
            # under the name of the function, it can access itself
            [node.name] + [a.arg for a in node.args.args],
            [plt.Var("f")] + [plt.Var(f"p{i}") for i in range(len(node.args.args))],
            plt.Var(STATEMONAD),
        )
        return plt.Lambda(
            [STATEMONAD],
            extend_statemonad(
                [node.name],
                [
                    plt.Lambda(
                        ["f"] + [f"p{i}" for i in range(len(node.args.args))],
                        plt.Apply(
                            compiled_return,
                            plt.Apply(
                                compiled_body,
                                args_state,
                            ),
                        ),
                    )
                ],
                plt.Var(STATEMONAD),
            ),
        )

    def visit_While(self, node: TypedWhile) -> plt.AST:
        compiled_c = self.visit(node.test)
        compiled_s = self.visit_sequence(node.body)
        if node.orelse:
            # If there is orelse, transform it to an appended sequence (TODO check if this is correct)
            cn = copy(node)
            cn.orelse = []
            return self.visit_sequence([cn] + node.orelse)
        # return rf"(\{STATEMONAD} -> let g = (\s f -> if ({compiled_c} s) then f ({compiled_s} s) f else s) in (g {STATEMONAD} g))"
        return plt.Lambda(
            [STATEMONAD],
            plt.Let(
                bindings=[
                    (
                        "g",
                        plt.Lambda(
                            ["s", "f"],
                            plt.Ite(
                                plt.Apply(compiled_c, plt.Var("s")),
                                plt.Apply(
                                    plt.Var("f"),
                                    plt.Apply(compiled_s, plt.Var("s")),
                                    plt.Var("f"),
                                ),
                                plt.Var("s"),
                            ),
                        ),
                    ),
                ],
                term=plt.Apply(plt.Var("g"), plt.Var(STATEMONAD), plt.Var("g")),
            ),
        )

    def visit_For(self, node: TypedFor) -> plt.AST:
        # TODO implement for list
        if isinstance(node.iter.typ, ListType):
            raise NotImplementedError(
                "Compilation of list iterators not implemented yet."
            )
        raise NotImplementedError("Compilation of raw for statements not supported")

    def visit_If(self, node: TypedIf) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            plt.Ite(
                plt.Apply(self.visit(node.test), plt.Var(STATEMONAD)),
                plt.Apply(self.visit_sequence(node.body), plt.Var(STATEMONAD)),
                plt.Apply(self.visit_sequence(node.orelse), plt.Var(STATEMONAD)),
            ),
        )

    def visit_Return(self, node: TypedReturn) -> plt.AST:
        raise NotImplementedError(
            "Compilation of return statements except for last statement in function is not supported."
        )

    def visit_Pass(self, node: TypedPass) -> plt.AST:
        return self.visit_sequence([])

    def visit_Subscript(self, node: TypedSubscript) -> plt.AST:
        assert isinstance(
            node.slice, Index
        ), "Only single index slices are currently supported"
        if isinstance(node.value.typ, TupleType):
            assert isinstance(
                node.slice.value, Constant
            ), "Only constant index access for tuples is supported"
            assert isinstance(node.ctx, Load), "Tuples are read-only"
            return plt.Lambda(
                [STATEMONAD],
                emulate_nth(
                    plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                    node.slice.value.value,
                    len(node.value.typ.typs),
                ),
            )
        if isinstance(node.value.typ, ListType):
            # rf'(\{STATEMONAD} -> let g = (\i xs f -> if (!NullList xs) then (!Trace "OOB" (Error ())) else (if i ==i 0 then (!HeadList xs) else f (i -i 1) (!TailList xs) f)) in (g ({compiled_i} {STATEMONAD}) ({compiled_v} {STATEMONAD}) g))'
            return plt.Lambda(
                [STATEMONAD],
                plt.Let(
                    [
                        (
                            "g",
                            plt.Lambda(
                                ["i", "xs", "f"],
                                plt.Ite(
                                    plt.Force(
                                        plt.Apply(
                                            plt.BuiltIn(BuiltInFun.NullList),
                                            plt.Var("xs"),
                                        )
                                    ),
                                    self.visit(
                                        TypedCall(
                                            TypedName("print", ctx=Load()),
                                            [
                                                TypedConstant(
                                                    "Out of bounds", InstanceType("str")
                                                )
                                            ],
                                        )
                                    ),
                                    plt.Ite(
                                        plt.Apply(
                                            plt.BuiltIn(BuiltInFun.EqualsInteger),
                                            plt.Var("i"),
                                            plt.Integer(0),
                                        ),
                                        plt.Force(
                                            plt.Apply(
                                                plt.BuiltIn(BuiltInFun.HeadList),
                                                plt.Var("xs"),
                                            )
                                        ),
                                        plt.Apply(
                                            plt.Var("f"),
                                            plt.Apply(
                                                plt.BuiltIn(BuiltInFun.SubtractInteger),
                                                plt.Var("i"),
                                                plt.Integer(1),
                                            ),
                                            plt.Force(
                                                plt.Apply(
                                                    plt.BuiltIn(BuiltInFun.TailList),
                                                    plt.Var("xs"),
                                                )
                                            ),
                                            plt.Var("f"),
                                        ),
                                    ),
                                ),
                            ),
                        )
                    ],
                    plt.Apply(
                        plt.Var("g"),
                        plt.Apply(self.visit(node.slice.value), plt.Var(STATEMONAD)),
                        plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                        plt.Var("g"),
                    ),
                ),
            )
        raise NotImplementedError(f"Could not implement subscript of {node}")

    def visit_Tuple(self, node: TypedTuple) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            plt.Tuple(
                *(plt.Apply(self.visit(e), plt.Var(STATEMONAD)) for e in node.elts)
            ),
        )

    def visit_ClassDef(self, node: ClassDef) -> plt.AST:
        return self.visit_sequence([])

    def visit_Attribute(self, node: TypedAttribute) -> plt.AST:
        # rewrite to access the field at position node.pos
        # (use the internal function for fields)
        return self.visit(
            TypedSubscript(
                value=TypedCall(
                    TypedName(
                        id="__fields__",
                        ctx=Load(),
                        typ=FunctionType([InstanceType], ListType([])),
                    ),
                    [node.value],
                    typ=ListType([]),
                ),
                slice=Index(
                    value=TypedConstant(value=node.pos, typ=InstanceType("int"))
                ),
                typ=node.typ,
            )
        )

    def generic_visit(self, node: AST) -> plt.AST:
        raise NotImplementedError(f"Can not compile {node}")


def compile(prog: AST):
    compiler_steps = [
        RewriteAugAssign,
        RewriteFor,
        RewriteTupleAssign,
        RewriteDataclasses,
        AggressiveTypeInferencer,
        UPLCCompiler,
    ]
    for s in compiler_steps:
        prog = s().visit(prog)
    return prog
