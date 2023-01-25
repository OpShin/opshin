import logging
from logging import getLogger
from ast import fix_missing_locations

from .rewrite.rewrite_augassign import RewriteAugAssign
from .rewrite.rewrite_forbidden_overwrites import RewriteForbiddenOverwrites
from .rewrite.rewrite_import import RewriteImport
from .rewrite.rewrite_import_dataclasses import RewriteImportDataclasses
from .rewrite.rewrite_import_hashlib import RewriteImportHashlib
from .rewrite.rewrite_import_plutusdata import RewriteImportPlutusData
from .rewrite.rewrite_import_typing import RewriteImportTyping
from .rewrite.rewrite_inject_builtins import RewriteInjectBuiltins
from .rewrite.rewrite_remove_type_stuff import RewriteRemoveTypeStuff
from .rewrite.rewrite_tuple_assign import RewriteTupleAssign
from .optimize.optimize_remove_pass import OptimizeRemovePass
from .optimize.optimize_remove_deadvars import OptimizeRemoveDeadvars
from .optimize.optimize_varlen import OptimizeVarlen
from .type_inference import *
from .util import CompilingNodeTransformer
from .typed_ast import transform_ext_params_map, transform_output_map, RawPlutoExpr


_LOGGER = logging.getLogger(__name__)

STATEMONAD = "s"


BinOpMap = {
    Add: {
        IntegerInstanceType: {
            IntegerInstanceType: plt.AddInteger,
        },
        ByteStringInstanceType: {
            ByteStringInstanceType: plt.AppendByteString,
        },
        StringInstanceType: {
            StringInstanceType: plt.AppendString,
        },
    },
    Sub: {
        IntegerInstanceType: {
            IntegerInstanceType: plt.SubtractInteger,
        }
    },
    Mult: {
        IntegerInstanceType: {
            IntegerInstanceType: plt.MultiplyInteger,
        }
    },
    Div: {
        IntegerInstanceType: {
            IntegerInstanceType: plt.DivideInteger,
        }
    },
    Mod: {
        IntegerInstanceType: {
            IntegerInstanceType: plt.ModInteger,
        }
    },
}


ConstantMap = {
    str: plt.Text,
    bytes: lambda x: plt.ByteString(x),
    int: lambda x: plt.Integer(x),
    bool: plt.Bool,
    type(None): lambda _: plt.Unit(),
}


def wrap_validator_double_function(x: plt.AST):
    """Wraps the validator function to enable a double function as minting script"""
    return plt.Lambda(
        ["a0", "a1"],
        plt.Ite(
            # if the second argument has constructor 0 = script context
            plt.DelayedChooseData(
                plt.Var("a1"),
                plt.EqualsInteger(plt.Constructor(plt.Var("a1")), plt.Integer(0)),
                plt.Bool(False),
                plt.Bool(False),
                plt.Bool(False),
                plt.Bool(False),
            ),
            # call the validator with a0, a1, and plug in Unit for data
            plt.Apply(x, plt.Unit(), plt.Var("a0"), plt.Var("a1")),
            # else call the validator with a0, a1 and return (now partially bound)
            plt.Apply(x, plt.Var("a0"), plt.Var("a1")),
        ),
    )


def extend_statemonad(
    names: typing.List[str],
    values: typing.List[plt.AST],
    old_statemonad: plt.FunctionalMap,
):
    return plt.FunctionalMapExtend(old_statemonad, [n for n in names], values)


INITIAL_STATE = plt.FunctionalMap()


class UPLCCompiler(CompilingNodeTransformer):
    """
    Expects a TypedAST and returns UPLC/Pluto like code
    """

    step = "Compiling python statements to UPLC"

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

    def visit_Compare(self, node: TypedCompare) -> plt.AST:
        assert len(node.ops) == 1, "Only single comparisons are supported"
        assert len(node.comparators) == 1, "Only single comparisons are supported"
        cmpop = node.ops[0]
        comparator = node.comparators[0].typ
        op = node.left.typ.cmp(cmpop, comparator)
        return plt.Lambda(
            [STATEMONAD],
            plt.Apply(
                op,
                plt.Apply(self.visit(node.left), plt.Var(STATEMONAD)),
                plt.Apply(self.visit(node.comparators[0]), plt.Var(STATEMONAD)),
            ),
        )

    def visit_Module(self, node: TypedModule) -> plt.AST:
        # find main function
        # TODO can use more sophisiticated procedure here i.e. functions marked by comment
        main_fun: typing.Optional[InstanceType] = None
        for s in node.body:
            if isinstance(s, FunctionDef) and s.orig_name == "validator":
                main_fun = s
        assert main_fun is not None, "Could not find function named validator"
        main_fun_typ: FunctionType = main_fun.typ.typ
        assert isinstance(
            main_fun_typ, FunctionType
        ), "Variable named validator is not of type function"

        # check if this is a contract written to double function
        enable_double_func_mint_spend = False
        if len(main_fun_typ.argtyps) == 3:
            # check if is possible
            second_arg = main_fun_typ.argtyps[1]
            assert isinstance(
                second_arg, InstanceType
            ), "Can not pass Class into validator"
            if isinstance(second_arg.typ, UnionType):
                possible_types = second_arg.typ.typs
            else:
                possible_types = [second_arg.typ]
            if any(isinstance(t, UnitType) for t in possible_types):
                _LOGGER.warning(
                    "The redeemer is annotated to be 'None'. This value is usually encoded in PlutusData with constructor id 0 and no fields. If you want the script to double function as minting and spending script, annotate the second argument with 'NoRedeemer'."
                )
            enable_double_func_mint_spend = not any(
                (isinstance(t, RecordType) and t.record.constructor != 0)
                or isinstance(t, UnitType)
                for t in possible_types
            )
            if not enable_double_func_mint_spend:
                _LOGGER.warning(
                    "The second argument to the validator function potentially has constructor id 0. The validator will not be able to double function as minting script and spending script."
                )

        validator = plt.Lambda(
            [f"p{i}" for i, _ in enumerate(main_fun_typ.argtyps)],
            transform_output_map(main_fun_typ.rettyp)(
                plt.Let(
                    [
                        (
                            "s",
                            plt.Apply(self.visit_sequence(node.body), INITIAL_STATE),
                        ),
                        (
                            "g",
                            plt.FunctionalMapAccess(
                                plt.Var("s"),
                                plt.ByteString(main_fun.name),
                                plt.TraceError("NameError: validator"),
                            ),
                        ),
                    ],
                    plt.Apply(
                        plt.Var("g"),
                        *[
                            transform_ext_params_map(a)(plt.Var(f"p{i}"))
                            for i, a in enumerate(main_fun_typ.argtyps)
                        ],
                        plt.Var("s"),
                    ),
                ),
            ),
        )
        if enable_double_func_mint_spend:
            validator = wrap_validator_double_function(validator)
        cp = plt.Program("1.0.0", validator)
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
        if isinstance(node.targets[0].typ, ClassType):
            # Assigning a class type to another class type is equivalent to a ClassDef - a nop
            return self.visit_sequence([])
        compiled_e = self.visit(node.value)
        # (\{STATEMONAD} -> (\x -> if (x ==b {self.visit(node.targets[0])}) then ({compiled_e} {STATEMONAD}) else ({STATEMONAD} x)))
        return plt.Lambda(
            [STATEMONAD],
            plt.FunctionalMapExtend(
                plt.Var(STATEMONAD),
                [node.targets[0].id],
                [plt.Apply(compiled_e, plt.Var(STATEMONAD))],
            ),
        )

    def visit_AnnAssign(self, node: AnnAssign) -> plt.AST:
        assert isinstance(
            node.target, Name
        ), "Assignments to other things then names are not supported"
        assert isinstance(
            node.target.typ, InstanceType
        ), "Can only assign instances to instances"
        compiled_e = self.visit(node.value)
        # we need to map this as it will originate from PlutusData
        # (\{STATEMONAD} -> (\x -> if (x ==b {self.visit(node.targets[0])}) then ({compiled_e} {STATEMONAD}) else ({STATEMONAD} x)))
        return plt.Lambda(
            [STATEMONAD],
            plt.FunctionalMapExtend(
                plt.Var(STATEMONAD),
                [node.target.id],
                [
                    transform_ext_params_map(node.target.typ)(
                        plt.Apply(compiled_e, plt.Var(STATEMONAD))
                    )
                ],
            ),
        )

    def visit_Name(self, node: TypedName) -> plt.AST:
        # depending on load or store context, return the value of the variable or its name
        if not isinstance(node.ctx, Load):
            raise NotImplementedError(f"Context {node.ctx} not supported")
        if isinstance(node.typ, ClassType):
            # if this is not an instance but a class, call the constructor
            return plt.Lambda(
                [STATEMONAD],
                node.typ.constr(),
            )
        return plt.Lambda(
            [STATEMONAD],
            plt.FunctionalMapAccess(
                plt.Var(STATEMONAD),
                plt.ByteString(node.id),
                plt.TraceError(f"NameError: {node.orig_id}"),
            ),
        )

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
        # TODO function is actually not of type polymorphic function type here anymore
        if isinstance(node.func.typ, PolymorphicFunctionInstanceType):
            # edge case for weird builtins that are polymorphic
            func_plt = node.func.typ.polymorphic_function.impl_from_args(
                node.func.typ.typ.argtyps
            )
        else:
            func_plt = plt.Apply(self.visit(node.func), plt.Var(STATEMONAD))
        return plt.Lambda(
            [STATEMONAD],
            plt.Apply(
                func_plt,
                # pass in all arguments evaluated with the statemonad
                *(plt.Apply(self.visit(a), plt.Var(STATEMONAD)) for a in node.args),
                # eventually pass in the state monad as well
                plt.Var(STATEMONAD),
            ),
        )

    def visit_FunctionDef(self, node: TypedFunctionDef) -> plt.AST:
        body = node.body.copy()
        if not isinstance(body[-1], Return):
            tr = Return(None)
            tr.typ = NoneInstanceType
            assert (
                node.typ.typ.rettyp == NoneInstanceType
            ), "Function has no return statement but is supposed to return not-None value"
            body.append(tr)
        compiled_body = self.visit_sequence(body[:-1])
        compiled_return = self.visit(body[-1].value)
        args_state = plt.FunctionalMapExtend(
            plt.Var(STATEMONAD),
            # the function can see its argument under the argument names
            [a.arg for a in node.args.args],
            [plt.Var(f"p{i}") for i in range(len(node.args.args))],
        )
        return plt.Lambda(
            [STATEMONAD],
            plt.FunctionalMapExtend(
                plt.Var(STATEMONAD),
                [node.name],
                [
                    plt.Lambda(
                        # expect the statemonad again -> this is the basis for internally available values
                        [f"p{i}" for i in range(len(node.args.args))] + [STATEMONAD],
                        plt.Apply(
                            compiled_return,
                            plt.Apply(
                                compiled_body,
                                args_state,
                            ),
                        ),
                    )
                ],
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
        if node.orelse:
            # If there is orelse, transform it to an appended sequence (TODO check if this is correct)
            cn = copy(node)
            cn.orelse = []
            return self.visit_sequence([cn] + node.orelse)
        assert isinstance(node.iter.typ, InstanceType)
        if isinstance(node.iter.typ.typ, ListType):
            assert isinstance(
                node.target, Name
            ), "Can only assign value to singleton element"
            return plt.Lambda(
                [STATEMONAD],
                plt.FoldList(
                    plt.Apply(self.visit(node.iter), plt.Var(STATEMONAD)),
                    plt.Lambda(
                        [STATEMONAD, "e"],
                        plt.Apply(
                            self.visit_sequence(node.body),
                            plt.FunctionalMapExtend(
                                plt.Var(STATEMONAD),
                                [node.target.id],
                                [plt.Var("e")],
                            ),
                        ),
                    ),
                    plt.Var(STATEMONAD),
                ),
            )
        raise NotImplementedError(
            "Compilation of for statements for anything but lists not implemented yet"
        )

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
            node.value.typ, InstanceType
        ), "Can only access elements of instances, not classes"
        if isinstance(node.value.typ.typ, TupleType):
            assert isinstance(
                node.slice, Index
            ), "Only single index slices for tuples are currently supported"
            assert isinstance(
                node.slice.value, Constant
            ), "Only constant index access for tuples is supported"
            assert isinstance(node.ctx, Load), "Tuples are read-only"
            return plt.Lambda(
                [STATEMONAD],
                plt.FunctionalTupleAccess(
                    plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                    node.slice.value.value,
                    len(node.value.typ.typ.typs),
                ),
            )
        if isinstance(node.value.typ.typ, ListType):
            assert isinstance(
                node.slice, Index
            ), "Only single index slices for lists are currently supported"
            assert (
                node.slice.value.typ == IntegerInstanceType
            ), "Only single element list index access supported"
            return plt.Lambda(
                [STATEMONAD],
                plt.IndexAccessList(
                    plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                    plt.Apply(self.visit(node.slice.value), plt.Var(STATEMONAD)),
                ),
            )
        elif isinstance(node.value.typ.typ, ByteStringType):
            if isinstance(node.slice, Index):
                return plt.Lambda(
                    [STATEMONAD],
                    plt.IndexByteString(
                        plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
                        plt.Apply(self.visit(node.slice.value), plt.Var(STATEMONAD)),
                    ),
                )
            elif isinstance(node.slice, Slice):
                return plt.Lambda(
                    [STATEMONAD],
                    plt.SliceByteString(
                        plt.Apply(self.visit(node.slice.lower), plt.Var(STATEMONAD)),
                        plt.SubtractInteger(
                            plt.Apply(
                                self.visit(node.slice.upper), plt.Var(STATEMONAD)
                            ),
                            plt.Integer(1),
                        ),
                        plt.Apply(self.visit(node.value), plt.Var(STATEMONAD)),
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

    def visit_ClassDef(self, node: TypedClassDef) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            plt.FunctionalMapExtend(
                plt.Var(STATEMONAD),
                [node.name],
                [node.class_typ.constr()],
            ),
        )

    def visit_Attribute(self, node: TypedAttribute) -> plt.AST:
        assert isinstance(
            node.typ, InstanceType
        ), "Can only access attributes of instances"
        obj = self.visit(node.value)
        attr = node.value.typ.attribute(node.attr)
        return plt.Lambda(
            [STATEMONAD], plt.Apply(attr, plt.Apply(obj, plt.Var(STATEMONAD)))
        )

    def visit_Assert(self, node: TypedAssert) -> plt.AST:
        return plt.Lambda(
            [STATEMONAD],
            plt.Ite(
                plt.Apply(self.visit(node.test), plt.Var(STATEMONAD)),
                plt.Var(STATEMONAD),
                plt.Apply(
                    plt.Error(),
                    plt.Trace(
                        plt.Apply(self.visit(node.msg), plt.Var(STATEMONAD)), plt.Unit()
                    )
                    if node.msg is not None
                    else plt.Unit(),
                ),
            ),
        )

    def visit_RawPlutoExpr(self, node: RawPlutoExpr) -> plt.AST:
        return node.expr

    def visit_List(self, node: TypedList) -> plt.AST:
        assert isinstance(node.typ, InstanceType)
        assert isinstance(node.typ.typ, ListType)
        l = empty_list(node.typ.typ.typ)
        for e in node.elts:
            l = plt.MkCons(plt.Apply(self.visit(e), plt.Var(STATEMONAD)), l)
        return plt.Lambda([STATEMONAD], l)

    def visit_Dict(self, node: TypedDict) -> plt.AST:
        assert isinstance(node.typ, InstanceType)
        assert isinstance(node.typ.typ, DictType)
        key_type = node.typ.typ.key_typ
        value_type = node.typ.typ.value_typ
        l = plt.EmptyDataPairList()
        for k, v in zip(node.keys, node.values):
            l = plt.MkCons(
                plt.MkPairData(
                    transform_output_map(key_type)(
                        plt.Apply(self.visit(k), plt.Var(STATEMONAD))
                    ),
                    transform_output_map(value_type)(
                        plt.Apply(self.visit(v), plt.Var(STATEMONAD))
                    ),
                ),
                l,
            )
        return plt.Lambda([STATEMONAD], l)

    def generic_visit(self, node: AST) -> plt.AST:
        raise NotImplementedError(f"Can not compile {node}")


def compile(prog: AST):
    rewrite_steps = [
        # Important to call this one first - it imports all further files
        RewriteImport,
        # Rewrites that simplify the python code
        RewriteAugAssign,
        RewriteTupleAssign,
        RewriteImportPlutusData,
        RewriteImportHashlib,
        RewriteImportTyping,
        RewriteForbiddenOverwrites,
        RewriteImportDataclasses,
        # The type inference needs to be run after complex python operations were rewritten
        AggressiveTypeInferencer,
        # Rewrites that circumvent the type inference or use its results
        RewriteRemoveTypeStuff,
        RewriteInjectBuiltins,
    ]
    for s in rewrite_steps:
        prog = s().visit(prog)
        prog = fix_missing_locations(prog)

    # from here on raw uplc may occur, so we dont attempt to fix locations
    compile_pipeline = [
        # Apply optimizations
        OptimizeRemoveDeadvars,
        OptimizeVarlen,
        OptimizeRemovePass,
        # the compiler runs last
        UPLCCompiler,
    ]
    for s in compile_pipeline:
        prog = s().visit(prog)

    return prog
