from enum import Enum

from .type_inference import *
from . import pluto_ast as plt, uplc_ast
from .rewrite_for import RewriteFor
from .rewrite_tuple_assign import RewriteTupleAssign
from .rewrite_augassign import RewriteAugAssign
from .rewrite_dataclass import RewriteDataclasses
from .uplc_ast import BuiltInFun

VARS = "v"
SUBVARS = "sv"
HEAP = "h"


class ReturnTupleElem(Enum):
    STATE_FLAG = 0
    LOCAL_VARS = 1
    HEAP = 2
    RETURN_VALUE = 3


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


def from_primitive_int(local_vars: plt.AST, p: plt.AST):
    return plt.from_primitive(
        p, plt.Apply(local_vars, INTEGER_ATTRIBUTE_VARNAME, plt.Unit())
    )


def from_primitive_bool(local_vars: plt.AST, p: plt.AST):
    return plt.from_primitive(
        p, plt.Apply(local_vars, BOOL_ATTRIBUTE_VARNAME, plt.Unit())
    )


def from_primitive_none(local_vars: plt.AST):
    return plt.Apply(local_vars, NONE_ATTRIBUTE_VARNAME, plt.Unit())


def state_flag(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.STATE_FLAG.value, RETURN_TUPLE_SIZE)


def local_vars(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.LOCAL_VARS.value, RETURN_TUPLE_SIZE)


def heap(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.HEAP.value, RETURN_TUPLE_SIZE)


def return_value(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.RETURN_VALUE.value, RETURN_TUPLE_SIZE)


def exception(ret: plt.AST):
    return plt.TupleAccess(ret, ReturnTupleElem.RETURN_VALUE.value, RETURN_TUPLE_SIZE)


def exception_isset(ret: plt.AST):
    return plt.EqualsInteger(state_flag(ret), plt.Integer(StateFlags.ABORT.value))


def normal_return(local_vars: plt.AST, heap: plt.AST, return_value: plt.AST):
    return plt.Tuple(
        plt.Integer(StateFlags.RETURN.value),
        local_vars,
        heap,
        return_value,
    )


def except_return(local_vars: plt.AST, heap: plt.AST, exception: plt.AST):
    return plt.Tuple(
        plt.Integer(StateFlags.ABORT.value),
        local_vars,
        heap,
        exception,
    )


# TODO make sure that only unmodified variables are returned
def MethodCall(
    wv: plt.WrappedValue,
    local_vars: plt.AST,
    heap: plt.AST,
    method_name: str,
    *args: plt.AST,
):
    return plt.Apply(
        plt.Apply(
            wv,
            method_name.encode(),
            plt.Lambda(
                ["self", [str(i) for i, _ in enumerate(args)], VARS, HEAP],
                # TODO exceptions could also be a bit more fancy wrapped objects
                except_return(plt.Var(VARS), plt.Var(HEAP), plt.Text("AttributeError")),
            ),
        ),
        wv,
        *args,
        local_vars,
        heap,
    )


def AttributeAccess(
    wv: plt.WrappedValue, local_vars: plt.AST, heap: plt.AST, attribute_name: str
):
    return MethodCall(wv, local_vars, heap, attribute_name)


def chain_except(a: plt.AST, b: plt.AST, c: plt.AST):
    """
    The monad combinator
    b/c must expect local vars, heap and return value of a as first two arguments
    """
    return plt.Apply(
        plt.Lambda(
            ["r"],
            plt.Ite(
                exception_isset(plt.Var("r")),
                plt.Apply(
                    c,
                    local_vars(plt.Var("r")),
                    heap(plt.Var("r")),
                    return_value(plt.Var("r")),
                ),
                plt.Apply(
                    b,
                    local_vars(plt.Var("r")),
                    heap(plt.Var("r")),
                    return_value(plt.Var("r")),
                ),
            ),
        ),
        a,
    )


def chain(a: plt.AST, *b: plt.AST):
    # clean but inefficient implementation
    if len(b) == 0:
        return a
    res = chain_except(
        a,
        b[0],
        plt.Lambda(
            [VARS, HEAP, "e"], except_return(plt.Var(VARS), plt.Var(HEAP), plt.Var("e"))
        ),
    )
    return chain(res, *b[1:])


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
        plt.Lambda(
            [VARS, HEAP, "r"], normal_return(plt.Var(VARS), plt.Var(HEAP), plt.Var("r"))
        ),
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
        ["self", "other", VARS, HEAP],
        chain(
            MethodCall(plt.Var("other"), plt.Var(VARS), plt.Var(HEAP), "__int__"),
            plt.Lambda(
                [VARS, HEAP, "other_int"],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    from_primitive_int(
                        plt.Var(VARS),
                        plt.AddInteger(
                            to_primitive_int(plt.Var("self")),
                            to_primitive_int(plt.Var("other_int")),
                        ),
                    ),
                ),
            ),
        ),
    ),
    "__sub__": Lambda(
        ["self", "other", VARS, HEAP],
        chain(
            MethodCall(plt.Var("other"), plt.Var(VARS), plt.Var(HEAP), "__int__"),
            plt.Lambda(
                [VARS, HEAP, "other_int"],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    from_primitive_int(
                        plt.Var(VARS),
                        plt.SubtractInteger(
                            to_primitive_int(plt.Var("self")),
                            to_primitive_int(plt.Var("other_int")),
                        ),
                    ),
                ),
            ),
        ),
    ),
    "__eq__": Lambda(
        ["self", "other", VARS, HEAP],
        chain_except(
            plt.MethodCall(plt.Var("other"), plt.Var(VARS), plt.Var(HEAP), "__int__"),
            plt.Lambda(
                [VARS, HEAP, "other_int"],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    from_primitive_bool(
                        plt.Var(VARS),
                        plt.EqualsInteger(
                            to_primitive_int(plt.Var("self")),
                            to_primitive_int(plt.Var("other_int")),
                        ),
                    ),
                ),
            ),
            plt.Lambda(
                [VARS, HEAP, "other_int"],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    from_primitive_bool(plt.Var(VARS), plt.Bool(False)),
                ),
            ),
        ),
    ),
    "__int__": Lambda(
        ["self", VARS, HEAP],
        normal_return(plt.Var(VARS), plt.Var(HEAP), plt.Var("self")),
    ),
    "__bool__": Lambda(
        ["self", VARS, HEAP],
        normal_return(
            plt.Var(VARS),
            plt.Var(HEAP),
            from_primitive_bool(
                plt.Var(VARS),
                plt.NotEqualsInteger(to_primitive_int(plt.Var("self")), plt.Integer(0)),
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
        ["self", "other", VARS, HEAP],
        chain(
            MethodCall(plt.Var("other"), plt.Var(VARS), plt.Var(HEAP), "__int__"),
            plt.Lambda(
                [VARS, HEAP, "other_int"],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    from_primitive_int(
                        plt.Var(VARS),
                        plt.AddInteger(
                            # shortcut because we know there wont be an exception here
                            to_primitive_int(
                                return_value(
                                    MethodCall(
                                        plt.Var("self"),
                                        plt.Var(VARS),
                                        plt.Var(HEAP),
                                        "__int__",
                                    )
                                )
                            ),
                            to_primitive_int(plt.Var("other_int")),
                        ),
                    ),
                ),
            ),
        ),
    ),
    "__sub__": Lambda(
        ["_", "self", "other", VARS, HEAP],
        chain(
            MethodCall(plt.Var("other"), plt.Var(VARS), plt.Var(HEAP), "__int__"),
            plt.Lambda(
                [VARS, HEAP, "other_int"],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    from_primitive_int(
                        plt.Var(VARS),
                        plt.SubtractInteger(
                            # shortcut because we know there wont be an exception here
                            to_primitive_int(
                                return_value(
                                    MethodCall(
                                        plt.Var("self"),
                                        plt.Var(VARS),
                                        plt.Var(HEAP),
                                        "__int__",
                                    )
                                )
                            ),
                            to_primitive_int(plt.Var("other_int")),
                        ),
                    ),
                ),
            ),
        ),
    ),
    "__eq__": Lambda(
        ["_", "self", "other", VARS, HEAP],
        chain_except(
            plt.MethodCall(plt.Var("other"), plt.Var(VARS), plt.Var(HEAP), "__bool__"),
            plt.Lambda(
                [VARS, HEAP, "other_bool"],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    from_primitive_bool(
                        plt.Var(VARS),
                        plt.EqualsBool(
                            to_primitive_bool(plt.Var("self")),
                            to_primitive_bool(plt.Var("other_bool")),
                        ),
                    ),
                ),
            ),
            plt.Lambda(
                [VARS, HEAP, "other_bool"],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    from_primitive_bool(plt.Var(VARS), plt.Bool(False)),
                ),
            ),
        ),
    ),
    "__int__": Lambda(
        ["_", "self", VARS, HEAP],
        normal_return(
            plt.Var(VARS),
            plt.Var(HEAP),
            from_primitive_int(
                plt.Var(HEAP),
                plt.Ite(
                    to_primitive_bool(plt.Var("self")), plt.Integer(1), plt.Integer(0)
                ),
            ),
        ),
    ),
    "__bool__": Lambda(
        ["_", "self", VARS, HEAP],
        normal_return(plt.Var(VARS), plt.Var(HEAP), plt.Var("self")),
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
        ["_", "self", VARS, HEAP],
        normal_return(
            plt.Var(VARS),
            plt.Var(HEAP),
            from_primitive_bool(plt.Var(VARS), plt.Bool(False)),
        ),
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

INITIAL_VARS = plt.extend_map(
    INITIAL_ATTRIBUTES.keys(),
    INITIAL_ATTRIBUTES.values(),
    plt.MutableMap(),
)
INITIAL_HEAP = plt.MutableMap()


PYTHON_BUILT_INS = {
    "None": plt.Lambda(
        [VARS, HEAP],
        normal_return(
            plt.Var(VARS),
            plt.Var(HEAP),
            from_primitive_none(plt.Var(VARS)),
        ),
    ),
    "print": plt.Lambda(
        ["_", "x", VARS, HEAP],
        normal_return(
            plt.Var(VARS),
            plt.Var(HEAP),
            plt.Apply(
                plt.Lambda(["a", "b"], plt.Var("b")),
                plt.Trace(
                    # TODO call str(x)
                    plt.Var("x"),
                    plt.Unit(),
                ),
                from_primitive_none(plt.Var(VARS)),
            ),
        ),
    ),
    "int": plt.Lambda(
        ["_", "x", VARS, HEAP],
        # TODO fall back to trying to parse str -> int
        MethodCall(plt.Var("x"), plt.Var(VARS), plt.Var(HEAP), "__int__"),
    ),
}


INITIAL_VARS = extend_statemonad(
    PYTHON_BUILT_INS.keys(),
    PYTHON_BUILT_INS.values(),
    INITIAL_VARS,
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
        s = normal_return(
            plt.Var(VARS), plt.Var(HEAP), from_primitive_none(plt.Var(VARS))
        )
        for n in node_seq:
            compiled_stmt = self.visit(n)
            # TODO also abort with return
            s = plt.Apply(
                plt.Lambda(
                    ["r"],
                    plt.Ite(
                        plt.EqualsInteger(
                            state_flag(plt.Var("r")),
                            plt.Integer(StateFlags.CONTINUE.value),
                        ),
                        plt.Apply(
                            compiled_stmt, local_vars(plt.Var("r")), heap(plt.Var("r"))
                        ),
                        # Either it is abort or return - in both cases, just return whatever that step returned
                        plt.Var("r"),
                    ),
                ),
                s,
            )
        return plt.Lambda([VARS, HEAP], s)

    def visit_BinOp(self, node: TypedBinOp) -> plt.AST:
        opmet = BinOpMap.get(type(node.op))
        if opmet is None:
            raise NotImplementedError(f"Operation {node.op} is not implemented")
        return plt.Lambda(
            [VARS, HEAP],
            chain(
                plt.Apply(self.visit(node.right), plt.Var(VARS), plt.Var(HEAP)),
                plt.Lambda(
                    [VARS, HEAP, "r"],
                    MethodCall(
                        self.visit(node.left),
                        plt.Var(VARS),
                        plt.Var(HEAP),
                        opmet,
                        plt.Var("r"),
                    ),
                ),
            ),
        )

    def visit_Compare(self, node: Compare) -> plt.AST:
        assert len(node.ops) == 1, "Only single comparisons are supported"
        assert len(node.comparators) == 1, "Only single comparisons are supported"
        opmet = CmpMap.get(type(node.ops[0]))
        if opmet is None:
            raise NotImplementedError(f"Operation {node.ops[0]} is not implemented")
        return plt.Lambda(
            [VARS, HEAP],
            chain(
                plt.Apply(
                    self.visit(node.comparators[0]), plt.Var(VARS), plt.Var(HEAP)
                ),
                plt.Lambda(
                    [VARS, HEAP, "r"],
                    MethodCall(
                        self.visit(node.left),
                        plt.Var(VARS),
                        plt.Var(HEAP),
                        opmet,
                        plt.Var("r"),
                    ),
                ),
            ),
        )

    def visit_Module(self, node: TypedModule) -> plt.AST:
        # TODO insert data un-wrapping for byte/int
        # TODO insert wrapping in wrapped value types
        # TODO pass program arguments to the validator
        cp = plt.Program(
            "0.0.1",
            try_catch(
                chain(
                    plt.Apply(
                        self.visit_sequence(node.body),
                        INITIAL_VARS,
                        INITIAL_HEAP,
                    ),
                    plt.Lambda(
                        [VARS, HEAP, "r"],
                        normal_return(
                            plt.Var(VARS),
                            plt.Var(HEAP),
                            # vm => Validator function missing
                            plt.Apply(
                                plt.Var("r"),
                                plt.ByteString("validator".encode("utf8")),
                                plt.Lambda(["_"], plt.Trace("vm", plt.Error())),
                            ),
                        ),
                    ),
                    plt.Lambda(
                        [VARS, HEAP, "g"],
                        # TODO program paramters need to be passed in here
                        plt.Apply(
                            plt.Var("g"), plt.Var("g"), plt.Var(VARS), plt.Var(HEAP)
                        ),
                    ),
                ),
                plt.Lambda(
                    [VARS, HEAP, "e"],
                    plt.Trace(
                        plt.Var("e"),
                        plt.Error(),
                    ),
                ),
            ),
        )
        return cp

    def visit_Constant(self, node: TypedConstant) -> plt.AST:
        plt_type = ConstantMap.get(type(node.value))
        if plt_type is None:
            raise NotImplementedError(
                f"Constants of type {type(node.value)} are not supported"
            )
        return plt.Lambda(
            [VARS, HEAP],
            normal_return(
                plt.Var(VARS),
                plt.Var(HEAP),
                plt_type(node.value),
            ),
        )

    def visit_NoneType(self, _: typing.Optional[typing.Any]) -> plt.AST:
        return plt.Lambda(
            [VARS, HEAP],
            normal_return(
                plt.Var(VARS), plt.Var(HEAP), from_primitive_none(plt.Var(VARS))
            ),
        )

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
            [VARS, HEAP],
            chain(
                plt.Apply(compiled_e, plt.Var(VARS), plt.Var(HEAP)),
                plt.Lambda(
                    [VARS, HEAP, "r"],
                    normal_return(
                        extend_statemonad(
                            [node.targets[0].id],
                            [plt.Var("r")],
                            plt.Var(VARS),
                        ),
                        plt.Var(HEAP),
                        from_primitive_none(plt.Var(VARS)),
                    ),
                ),
            ),
        )

    def visit_Name(self, node: TypedName) -> plt.AST:
        # depending on load or store context, return the value of the variable or its name
        if isinstance(node.ctx, Load):
            return plt.Lambda(
                [VARS, HEAP],
                normal_return(
                    plt.Var(VARS),
                    plt.Var(HEAP),
                    # vnd => Variable name not defined yet
                    plt.Apply(
                        plt.Var(VARS),
                        plt.ByteString(node.id.encode()),
                        plt.Lambda(["_"], plt.Trace("vnd", plt.Error())),
                    ),
                ),
            )
        raise NotImplementedError(f"Context {node.ctx} not supported")

    def visit_Expr(self, node: TypedExpr) -> plt.AST:
        return plt.Lambda(
            [VARS, HEAP],
            chain(
                plt.Apply(self.visit(node.value), plt.Var(VARS), plt.Var(HEAP)),
                plt.Lambda(
                    [VARS, HEAP, "_"],
                    normal_return(
                        plt.Var(VARS),
                        plt.Var(HEAP),
                        from_primitive_none(plt.Var(VARS)),
                    ),
                ),
            ),
        )

    def visit_Call(self, node: TypedCall) -> plt.AST:
        # compiled_args = " ".join(f"({self.visit(a)} {STATEMONAD})" for a in node.args)
        # return rf"(\{STATEMONAD} -> ({self.visit(node.func)} {compiled_args})"
        return plt.Lambda(
            [VARS, HEAP],
            chain(
                plt.Apply(self.visit(node.func), plt.Var(VARS), plt.Var(HEAP)),
                plt.Lambda(
                    [VARS, HEAP, "g"],
                    normal_return(
                        plt.Var(VARS),
                        plt.Var(HEAP),
                        plt.Apply(
                            plt.Var("g"),
                            # pass the function to itself for recursion
                            plt.Var("g"),
                        ),
                    ),
                ),
                *(
                    plt.Lambda(
                        [VARS, HEAP, "g"],
                        chain(
                            plt.Apply(self.visit(a), plt.Var(VARS), plt.Var(HEAP)),
                            plt.Lambda(
                                [VARS, HEAP, "a"],
                                normal_return(
                                    plt.Var(VARS),
                                    plt.Var(HEAP),
                                    plt.Apply(plt.Var("g"), plt.Var("a")),
                                ),
                            ),
                        ),
                    )
                    for a in node.args
                ),
                # finally pass the statemonad from the last argument to the function being called
                plt.Lambda(
                    [VARS, HEAP, "g"],
                    plt.Apply(plt.Var("g"), plt.Var(VARS), plt.Var(HEAP)),
                ),
            ),
        )

    def visit_FunctionDef(self, node: TypedFunctionDef) -> plt.AST:
        body = node.body.copy()
        compiled_body = self.visit_sequence(body)
        args_state = extend_statemonad(
            # under the name of the function, it can access itself
            [node.name] + [a.arg for a in node.args.args],
            [plt.Var("f")] + [plt.Var(f"p{i}") for i in range(len(node.args.args))],
            plt.Var(VARS),
        )
        return plt.Lambda(
            [VARS, HEAP],
            normal_return(
                extend_statemonad(
                    [node.name],
                    [
                        plt.Lambda(
                            ["f"]
                            + [f"p{i}" for i in range(len(node.args.args))]
                            + [VARS, HEAP],
                            chain(
                                # calls the function that will return a triple
                                plt.Apply(compiled_body, args_state, plt.Var(HEAP)),
                                # if successful, clean return flag and return ORIGINAL local vars, as well as MODIFIED heap
                                plt.Lambda(
                                    [SUBVARS, HEAP, "r"],
                                    normal_return(
                                        plt.Var(VARS),
                                        plt.Var(HEAP),
                                        plt.Var("r"),
                                    ),
                                ),
                            ),
                        )
                    ],
                    plt.Var(VARS),
                ),
                plt.Var(HEAP),
                from_primitive_none(plt.Var(VARS)),
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
            [VARS, HEAP],
            plt.Let(
                bindings=[
                    (
                        "g",
                        plt.Lambda(
                            [VARS, HEAP, "f"],
                            chain(
                                plt.Apply(compiled_c, plt.Var(VARS), plt.Var(HEAP)),
                                plt.Lambda(
                                    [VARS, HEAP, "cond"],
                                    plt.Ite(
                                        from_primitive_bool(
                                            plt.Var(VARS), plt.Var("cond")
                                        ),
                                        chain(
                                            plt.Apply(
                                                compiled_s, plt.Var(VARS), plt.Var(HEAP)
                                            ),
                                            plt.Lambda(
                                                [VARS, HEAP, "_"],
                                                plt.Apply(
                                                    plt.Var("f"),
                                                    plt.Var(VARS),
                                                    plt.Var(HEAP),
                                                    plt.Var("f"),
                                                ),
                                            ),
                                        ),
                                        normal_return(
                                            plt.Var(VARS),
                                            plt.Var(HEAP),
                                            from_primitive_none(plt.Var(VARS)),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ],
                term=plt.Apply(
                    plt.Var("g"), plt.Var(VARS), plt.Var(HEAP), plt.Var("g")
                ),
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
