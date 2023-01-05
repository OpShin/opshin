from enum import Enum
from ast import parse

from .type_inference import *
from .rewrite_for import RewriteFor
from .rewrite_tuple_assign import RewriteTupleAssign
from .rewrite_augassign import RewriteAugAssign
from .rewrite_import_plutusdata import RewriteImportPlutusData
from .rewrite_import_typing import RewriteImportTyping
from .rewrite_import import RewriteImport

import pluthon as plt
from uplc.uplc_ast import BuiltInFun

STATEMONAD = "s"


BinOpMap = {
    Add: {
        IntegerType: {
            IntegerType: {
                plt.AddInteger,
            }
        },
        ByteStringType: {
            ByteStringType: plt.AppendByteString,
        },
    },
    Sub: {
        IntegerType: {
            IntegerType: plt.SubtractInteger,
        }
    },
    Mult: {
        IntegerType: {
            IntegerType: plt.MultiplyInteger,
        }
    },
    Div: {
        IntegerType: {
            IntegerType: plt.DivideInteger,
        }
    },
    Mod: {
        IntegerType: {
            IntegerType: plt.ModInteger,
        }
    },
}

CmpMap = {
    Eq: {
        IntegerType: {
            IntegerType: {
                plt.EqualsInteger,
            }
        },
        ByteStringType: {
            ByteStringType: {
                plt.EqualsByteString,
            }
        },
        BoolType: {
            BoolType: {
                plt.EqualsBool,
            }
        },
    },
    Lt: {
        IntegerType: {
            IntegerType: {
                BuiltInFun.LessThanInteger,
            }
        },
    },
}

ConstantMap = {
    str: plt.Text,
    bytes: plt.ByteString,
    int: plt.Integer,
    bool: plt.Bool,
    type(None): lambda _: plt.NoneData(),
}


def extend_statemonad(
    names: typing.List[str],
    values: typing.List[plt.AST],
    old_statemonad: plt.FunctionalMap,
):
    return plt.FunctionalMapExtend(old_statemonad, [n.encode() for n in names], values)


class PythonBuiltIn(Enum):
    print = plt.Lambda(
        ["f", "x", STATEMONAD],
        plt.Trace(plt.Var("x"), plt.NoneData()),
    )
    range = plt.Lambda(["f", "limit", STATEMONAD], plt.Range(plt.Var("limit")))


INITIAL_STATE = extend_statemonad(
    [b.name for b in PythonBuiltIn],
    [b.value for b in PythonBuiltIn],
    plt.FunctionalMap(),
)


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
            s = plt.Apply(compiled_stmt, s)
        return plt.Lambda([STATEMONAD], s)

    def visit_BinOp(self, node: TypedBinOp) -> plt.AST:
        opmap = BinOpMap.get(type(node.op))
        if opmap is None:
            raise NotImplementedError(f"Operation {node.op} is not implemented")
        opmap2 = opmap.get(node.left.typ)
        if opmap2 is None:
            raise NotImplementedError(
                f"Operation {node.op} is not implemented for left type {node.left.typ}"
            )
        op = opmap2.get(node.right.typ)
        if opmap2 is None:
            raise NotImplementedError(
                f"Operation {node.op} is not implemented for left type {node.left.typ} and right type {node.right.typ}"
            )
        return plt.Lambda(
            [STATEMONAD],
            op(
                plt.Apply(self.visit(node.left), plt.Var(STATEMONAD)),
                plt.Apply(self.visit(node.right), plt.Var(STATEMONAD)),
            ),
        )

    def visit_Compare(self, node: Compare) -> plt.AST:
        assert len(node.ops) == 1, "Only single comparisons are supported"
        assert len(node.comparators) == 1, "Only single comparisons are supported"
        opmap = CmpMap.get(type(node.ops[0]))
        if opmap is None:
            raise NotImplementedError(f"Operation {node.ops[0]} is not implemented")
        opmap2 = opmap.get(node.left.typ)
        if opmap2 is None:
            raise NotImplementedError(
                f"Operation {node.ops[0]} is not implemented for left type {node.left.typ}"
            )
        op = opmap2.get(node.comparators[0].typ)
        if op is None:
            raise NotImplementedError(
                f"Operation {node.ops[0]} is not implemented for left type {node.left.typ} and right type {node.comparators[0].typ}"
            )
        return plt.Lambda(
            [STATEMONAD],
            op(
                plt.Apply(self.visit(node.left), plt.Var(STATEMONAD)),
                plt.Apply(self.visit(node.comparators[0]), plt.Var(STATEMONAD)),
            ),
        )

    def visit_Module(self, node: TypedModule) -> plt.AST:
        cp = plt.Program(
            "0.0.1",
            # TODO directly unwrap supposedly int/byte data? how?
            plt.Let(
                [
                    (
                        "g",
                        plt.Apply(
                            plt.Apply(self.visit_sequence(node.body), INITIAL_STATE),
                            plt.ByteString("main".encode("utf8")),
                        ),
                    )
                ],
                plt.Apply(plt.Var("g"), plt.Var("g")),
            ),
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
        return plt.Lambda([STATEMONAD], plt.Unit())

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
                plt.FunctionalMapAccess(
                    plt.Var(STATEMONAD),
                    plt.ByteString(node.id.encode()),
                    plt.Trace("NameError", plt.Error()),
                ),
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
                plt.FunctionalTupleAccess(
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
            plt.FunctionalTuple(
                *(plt.Apply(self.visit(e), plt.Var(STATEMONAD)) for e in node.elts)
            ),
        )

    def visit_ClassDef(self, node: ClassDef) -> plt.AST:
        # TODO add initializer to state monad
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
        # Important to call this one first - it imports all further files
        RewriteImport,
        # The remaining order is almost arbitrary
        RewriteAugAssign,
        RewriteFor,
        RewriteTupleAssign,
        RewriteImportPlutusData,
        RewriteImportTyping,
        AggressiveTypeInferencer,
        UPLCCompiler,
    ]
    for s in compiler_steps:
        prog = s().visit(prog)
    return prog
