import ast
import copy
import io
import math
import re
import tokenize
import typing
from dataclasses import dataclass
from ast import Load, Name, Constant, Slice

import pluthon as plt
import uplc.ast as uplc
from pycardano import PlutusData
from uplc.ast import data_from_cbor

from .bridge import to_uplc_builtin
from .optimize.optimize_remove_trace import OptimizeRemoveTrace
from .prelude import Nothing
from .rewrite.rewrite_import_bls12_381 import RewriteImportBLS12381
from .type_impls import (
    InstanceType,
    DataInstanceType,
    UnionType,
    UnitType,
    Type,
    RecordType,
    transform_ext_params_map,
    AnyType,
    transform_output_map,
    ClassType,
    PolymorphicFunctionInstanceType,
    ListType,
    TupleType,
    PairType,
    RawTupleType,
    BoolInstanceType,
    IntegerInstanceType,
    empty_list,
    DictType,
    ByteStringType,
    FunctionType,
    OUnit,
    UnitInstanceType,
)
from .type_inference import map_to_orig_name, AggressiveTypeInferencer
from .typed_ast import *

from .compiler_config import DEFAULT_CONFIG
from .optimize.optimize_const_folding import OptimizeConstantFolding
from .rewrite.rewrite_expanded_union_calls import (
    RewriteExpandedUnionCalls,
)
from .rewrite.rewrite_function_closures import (
    RewriteFunctionClosures,
)
from .optimize.optimize_remove_deadconstants import OptimizeRemoveDeadConstants
from .optimize.optimize_remove_deadconds import OptimizeRemoveDeadConditions
from .optimize.optimize_fold_if_fallthrough import OptimizeFoldIfFallthrough
from .optimize.optimize_selective_narrowing import OptimizeSelectiveNarrowing
from .optimize.analyze_integrity import AnalyzeIntegrity
from .optimize.optimize_remove_checked_integrity_checks import (
    OptimizeRemoveCheckedIntegrityChecks,
)
from .optimize.optimize_remove_unreachable import OptimizeRemoveUnreachable
from .optimize.optimize_union_expansion import OptimizeUnionExpansion
from .optimize.optimize_fold_bool import OptimizeFoldBoolCast
from .optimize.optimize_bool_only_ops import OptimizeBoolOnlyOps

from .rewrite.rewrite_assert_none import RewriteAssertNone
from .rewrite.rewrite_adjacent_inline import RewriteAdjacentInline
from .rewrite.rewrite_annotate_fallthrough import RewriteAnnotateFallthrough
from .rewrite.rewrite_augassign import RewriteAugAssign
from .rewrite.rewrite_cast_condition import RewriteConditions
from .rewrite.rewrite_empty_dicts import RewriteEmptyDicts
from .rewrite.rewrite_empty_lists import RewriteEmptyLists
from .rewrite.rewrite_destructuring_assign import RewriteDestructuringAssign
from .rewrite.rewrite_forbidden_overwrites import RewriteForbiddenOverwrites
from .rewrite.rewrite_forbidden_return import RewriteForbiddenReturn
from .rewrite.rewrite_import import RewriteImport
from .rewrite.rewrite_import_dataclasses import RewriteImportDataclasses
from .rewrite.rewrite_import_hashlib import RewriteImportHashlib
from .rewrite.rewrite_import_integrity_check import RewriteImportIntegrityCheck
from .rewrite.rewrite_import_plutusdata import RewriteImportPlutusData
from .rewrite.rewrite_import_typing import RewriteImportTyping
from .rewrite.rewrite_import_uplc_builtins import RewriteImportUPLCBuiltins
from .rewrite.rewrite_inject_builtins import RewriteInjectBuiltins
from .rewrite.rewrite_orig_name import RewriteOrigName
from .rewrite.rewrite_remove_type_stuff import RewriteRemoveTypeStuff
from .rewrite.rewrite_scoping import RewriteScoping
from .rewrite.rewrite_subscript38 import RewriteSubscript38
from .rewrite.rewrite_tuple_assign import RewriteTupleAssign
from .optimize.optimize_remove_pass import OptimizeRemovePass
from .optimize.optimize_remove_deadvars import OptimizeRemoveDeadvars, NameLoadCollector
from .util import (
    CompilingNodeTransformer,
    NoOp,
    OVar,
    OLambda,
    OLet,
    OPSHIN_LOGGER,
    all_vars,
    SafeOLambda,
    opshin_name_scheme_compatible_varname,
    force_params,
    SafeApply,
    SafeLambda,
    written_vars,
    custom_fix_missing_locations,
)


@dataclass(frozen=True)
class ValidatorSignature:
    arguments: typing.Tuple[typing.Tuple[str, Type], ...]
    return_type: Type


def _extract_validator_signature(
    prog: TypedModule, validator_function_name: str
) -> ValidatorSignature:
    validators = [
        statement
        for statement in prog.body
        if isinstance(statement, ast.FunctionDef)
        and statement.orig_name == validator_function_name
    ]
    assert validators, (
        f"Contract has no function called '{validator_function_name}'. Make sure the "
        "compiled contract contains the requested function."
    )
    validator = validators[-1]
    assert isinstance(validator.typ, InstanceType) and isinstance(
        validator.typ.typ, FunctionType
    ), f"Variable named {validator_function_name} is not of type function"
    return ValidatorSignature(
        tuple((arg.orig_arg, arg.typ) for arg in validator.args.args),
        validator.typ.typ.rettyp,
    )


def needs_data_cast(typ: Type) -> bool:
    if not isinstance(typ, InstanceType):
        return False
    if isinstance(typ, DataInstanceType):
        return True
    if isinstance(typ.typ, (AnyType, UnionType)):
        return True
    if isinstance(typ.typ, ListType):
        return needs_data_cast(typ.typ.typ)
    if isinstance(typ.typ, DictType):
        return needs_data_cast(typ.typ.key_typ) or needs_data_cast(typ.typ.value_typ)
    return False


def transform_output_to_type(source: Type, target: Type):
    assert isinstance(source, InstanceType), "Can only transform instance types"
    assert isinstance(target, InstanceType), "Can only transform instance types"
    if isinstance(target, DataInstanceType):
        return transform_output_map(source)
    if isinstance(target.typ, (AnyType, UnionType)):
        return transform_output_map(source)
    if isinstance(target.typ, ListType) and isinstance(source.typ, ListType):
        if not needs_data_cast(target.typ.typ):
            return lambda x: x
        return lambda x: plt.MapList(
            x,
            OLambda(
                ["x"],
                transform_output_to_type(source.typ.typ, target.typ.typ)(OVar("x")),
            ),
            empty_list(target.typ.typ),
        )
    if isinstance(target.typ, DictType) and isinstance(source.typ, DictType):
        if not (
            needs_data_cast(target.typ.key_typ) or needs_data_cast(target.typ.value_typ)
        ):
            return lambda x: x
        return lambda x: plt.MapList(
            x,
            OLambda(
                ["x"],
                plt.MkPairData(
                    transform_output_map(target.typ.key_typ)(
                        transform_output_to_type(
                            source.typ.key_typ, target.typ.key_typ
                        )(
                            transform_ext_params_map(source.typ.key_typ)(
                                plt.FstPair(OVar("x"))
                            )
                        )
                    ),
                    transform_output_map(target.typ.value_typ)(
                        transform_output_to_type(
                            source.typ.value_typ, target.typ.value_typ
                        )(
                            transform_ext_params_map(source.typ.value_typ)(
                                plt.SndPair(OVar("x"))
                            )
                        )
                    ),
                ),
            ),
            plt.EmptyDataPairList(),
        )
    return lambda x: x


def rec_constant_map_data(c):
    if isinstance(c, bool):
        return uplc.PlutusInteger(int(c))
    if isinstance(c, int):
        return uplc.PlutusInteger(c)
    if isinstance(c, type(None)):
        return uplc.PlutusConstr(0, [])
    if isinstance(c, bytes):
        return uplc.PlutusByteString(c)
    if isinstance(c, str):
        return uplc.PlutusByteString(c.encode())
    if isinstance(c, list):
        return uplc.PlutusList([rec_constant_map_data(ce) for ce in c])
    if isinstance(c, dict):
        return uplc.PlutusMap(
            dict(
                zip(
                    (rec_constant_map_data(ce) for ce in c.keys()),
                    (rec_constant_map_data(ce) for ce in c.values()),
                )
            )
        )
    # This can occur when PlutusData is generated during constant folding
    if isinstance(c, PlutusData):
        return data_from_cbor(c.to_cbor())
    raise NotImplementedError(f"Unsupported constant type {type(c)}")


def rec_constant_map(c):
    if isinstance(c, bool):
        return uplc.BuiltinBool(c)
    if isinstance(c, int):
        return uplc.BuiltinInteger(c)
    if isinstance(c, type(None)):
        return uplc.BuiltinUnit()
    if isinstance(c, bytes):
        return uplc.BuiltinByteString(c)
    if isinstance(c, str):
        return uplc.BuiltinString(c)
    if isinstance(c, list):
        return uplc.BuiltinList([rec_constant_map(ce) for ce in c])
    if isinstance(c, dict):
        return uplc.BuiltinList(
            [
                uplc.BuiltinPair(*p)
                for p in zip(
                    (rec_constant_map_data(ce) for ce in c.keys()),
                    (rec_constant_map_data(ce) for ce in c.values()),
                )
            ]
        )
    # This can occur when PlutusData is generated during constant folding
    if isinstance(c, PlutusData):
        return data_from_cbor(c.to_cbor())
    raise NotImplementedError(f"Unsupported constant type {type(c)}")


def wrap_validator_double_function(x: plt.AST, pass_through: int = 0):
    """
    Wraps the validator function to enable a double function as minting script

    pass_through defines how many parameters x would normally take and should be passed through to x
    """
    return OLambda(
        [f"v{i}" for i in range(pass_through)] + ["a0", "a1"],
        OLet(
            [("p", plt.Apply(x, *(OVar(f"v{i}") for i in range(pass_through))))],
            plt.Ite(
                # if the second argument has constructor 0 = script context
                plt.DelayedChooseData(
                    OVar("a1"),
                    plt.EqualsInteger(plt.Constructor(OVar("a1")), plt.Integer(0)),
                    plt.Bool(False),
                    plt.Bool(False),
                    plt.Bool(False),
                    plt.Bool(False),
                ),
                # call the validator with a0, a1, and plug in "Nothing" for data
                plt.Apply(
                    OVar("p"),
                    plt.UPLCConstant(to_uplc_builtin(Nothing())),
                    OVar("a0"),
                    OVar("a1"),
                ),
                # else call the validator with a0, a1 and return (now partially bound)
                plt.Apply(OVar("p"), OVar("a0"), OVar("a1")),
            ),
        ),
    )


CallAST = typing.Callable[[plt.AST], plt.AST]


def _clamp_integer(value: plt.AST, lower: plt.AST, upper: plt.AST) -> plt.AST:
    return plt.Ite(
        plt.LessThanInteger(value, lower),
        lower,
        plt.Ite(plt.LessThanInteger(upper, value), upper, value),
    )


def _normalize_slice_index(
    raw_index: plt.AST, length: plt.AST, lower: plt.AST, upper: plt.AST
) -> plt.AST:
    return OLet(
        [
            (
                "adjusted_slice_index",
                plt.Ite(
                    plt.LessThanInteger(raw_index, plt.Integer(0)),
                    plt.AddInteger(raw_index, length),
                    raw_index,
                ),
            )
        ],
        _clamp_integer(OVar("adjusted_slice_index"), lower, upper),
    )


def _normalize_forward_slice_index(raw_index: plt.AST, length: plt.AST) -> plt.AST:
    return OLet(
        [
            (
                "adjusted_slice_index",
                plt.Ite(
                    plt.LessThanInteger(raw_index, plt.Integer(0)),
                    plt.AddInteger(raw_index, length),
                    raw_index,
                ),
            )
        ],
        plt.Ite(
            plt.LessThanEqualsInteger(OVar("adjusted_slice_index"), plt.Integer(0)),
            plt.Integer(0),
            OVar("adjusted_slice_index"),
        ),
    )


def _slice_list_contiguous(
    xs: plt.AST, start: plt.AST, stop: plt.AST, empty: plt.AST
) -> plt.AST:
    return plt.Ite(
        plt.LessThanEqualsInteger(stop, start),
        empty,
        plt.SliceList(
            start,
            plt.SubtractInteger(stop, start),
            xs,
            empty,
        ),
    )


def _slice_list_positive_stride(
    xs: plt.AST,
    start: plt.AST,
    stop: plt.AST,
    step: plt.AST,
    empty: plt.AST,
) -> plt.AST:
    stride = plt.RecFun(
        OLambda(
            ["stride", "remaining_xs", "remaining_length"],
            plt.Ite(
                plt.LessThanEqualsInteger(OVar("remaining_length"), plt.Integer(0)),
                empty,
                plt.IteNullList(
                    OVar("remaining_xs"),
                    empty,
                    plt.MkCons(
                        plt.HeadList(OVar("remaining_xs")),
                        plt.Apply(
                            OVar("stride"),
                            OVar("stride"),
                            plt.DropList(OVar("remaining_xs"), step, empty),
                            plt.SubtractInteger(OVar("remaining_length"), step),
                        ),
                    ),
                ),
            ),
        )
    )
    return plt.Ite(
        plt.LessThanEqualsInteger(stop, start),
        empty,
        plt.Apply(
            stride,
            plt.DropList(xs, start, empty),
            plt.SubtractInteger(stop, start),
        ),
    )


def _reverse_list(xs: plt.AST, empty: plt.AST) -> plt.AST:
    return plt.FoldList(
        xs,
        OLambda(["reversed_xs", "x"], plt.MkCons(OVar("x"), OVar("reversed_xs"))),
        empty,
    )


def _slice_bytes_contiguous(bs: plt.AST, start: plt.AST, stop: plt.AST) -> plt.AST:
    return plt.Ite(
        plt.LessThanEqualsInteger(stop, start),
        plt.ByteString(b""),
        plt.SliceByteString(start, plt.SubtractInteger(stop, start), bs),
    )


def _slice_bytes_stride(
    bs: plt.AST,
    start: plt.AST,
    stop: plt.AST,
    step: plt.AST,
    positive: bool,
) -> plt.AST:
    in_bounds = (
        plt.LessThanInteger(OVar("slice_index"), stop)
        if positive
        else plt.LessThanInteger(stop, OVar("slice_index"))
    )
    stride = plt.RecFun(
        OLambda(
            ["stride", "slice_index"],
            plt.Ite(
                in_bounds,
                plt.ConsByteString(
                    plt.IndexByteString(bs, OVar("slice_index")),
                    plt.Apply(
                        OVar("stride"),
                        OVar("stride"),
                        plt.AddInteger(OVar("slice_index"), step),
                    ),
                ),
                plt.ByteString(b""),
            ),
        )
    )
    return plt.Apply(stride, start)


class PlutoCompiler(CompilingNodeTransformer):
    """
    Expects a TypedAST and returns UPLC/Pluto like code
    """

    step = "Compiling python statements to UPLC"

    def __init__(
        self,
        validator_function_name="validator",
        config=DEFAULT_CONFIG,
    ):
        # parameters
        self.validator_function_name = validator_function_name
        self.config = config
        assert (
            self.config.fast_access_skip is None or self.config.fast_access_skip > 1
        ), "Parameter fast-access-skip needs to be greater than 1 or omitted"
        # marked knowledge during compilation
        self.current_function_typ: typing.List[FunctionType] = []
        self._destructure_id = 0

    def visit_sequence(self, node_seq: typing.List[typedstmt]) -> CallAST:
        def g(s: plt.AST):
            for n in reversed(node_seq):
                compiled_stmt = self.visit(n)
                s = compiled_stmt(s)
            return s

        return g

    def _assign_name_from_compiled_expr(
        self,
        target: TypedName,
        source_typ: Type,
        compiled_e: plt.AST,
    ) -> CallAST:
        assert isinstance(
            target, Name
        ), "Assignments to other things then names are not supported"
        if needs_data_cast(target.typ):
            compiled_e = transform_output_to_type(source_typ, target.typ)(compiled_e)
        varname = target.id
        return lambda x: plt.Let(
            [
                (opshin_name_scheme_compatible_varname(varname), compiled_e),
                (varname, plt.Delay(OVar(varname))),
            ],
            x,
        )

    def _bind_target_from_compiled_expr(
        self,
        target: typedexpr,
        source_typ: Type,
        compiled_e: plt.AST,
        body: plt.AST,
    ) -> plt.AST:
        if isinstance(target, Name):
            return self._assign_name_from_compiled_expr(target, source_typ, compiled_e)(
                body
            )
        assert isinstance(
            target, ast.Tuple
        ), "Only tuple destructuring targets are supported"
        deconstruct_typ = (
            source_typ.typ if isinstance(source_typ, InstanceType) else source_typ
        )
        source_name = f"destruct_{self._destructure_id}"
        self._destructure_id += 1

        def bind_fixed_arity(access_fn: typing.Callable[[int], plt.AST]) -> plt.AST:
            wrapped = body
            for index, element_target in reversed(list(enumerate(target.elts))):
                wrapped = self._bind_target_from_compiled_expr(
                    element_target,
                    element_target.typ,
                    access_fn(index),
                    wrapped,
                )
            return OLet([(source_name, compiled_e)], wrapped)

        if isinstance(deconstruct_typ, RawTupleType):
            pass
        elif isinstance(deconstruct_typ, TupleType):
            tuple_length = len(deconstruct_typ.typs)
            return bind_fixed_arity(
                lambda index: plt.FunctionalTupleAccess(
                    OVar(source_name), index, tuple_length
                )
            )
        elif isinstance(deconstruct_typ, PairType):
            return bind_fixed_arity(
                lambda index: transform_ext_params_map(target.elts[index].typ)(
                    (plt.FstPair if index == 0 else plt.SndPair)(OVar(source_name))
                )
            )

        assert isinstance(
            deconstruct_typ, (ListType, RawTupleType)
        ), "Expected tuple, pair, raw tuple, or list deconstruction"
        skip_element_null_checks = bool(self.config.remove_trace)

        def compile_element(index: int, list_name: str, result: plt.AST) -> plt.AST:
            if index >= len(target.elts):
                return plt.IteNullList(
                    OVar(list_name),
                    result,
                    plt.TraceError("ValueError: too many values to unpack"),
                )
            element_name = f"{source_name}_element_{index}"
            tail_name = f"{source_name}_rest_{index}"
            element_expr = OVar(element_name)
            if isinstance(deconstruct_typ, RawTupleType):
                element_expr = transform_ext_params_map(target.elts[index].typ)(
                    element_expr
                )
            bind_next = OLet(
                [
                    (element_name, plt.HeadList(OVar(list_name))),
                    (tail_name, plt.TailList(OVar(list_name))),
                ],
                self._bind_target_from_compiled_expr(
                    target.elts[index],
                    target.elts[index].typ,
                    element_expr,
                    compile_element(index + 1, tail_name, result),
                ),
            )
            if skip_element_null_checks:
                return bind_next
            return plt.IteNullList(
                OVar(list_name),
                plt.TraceError("ValueError: not enough values to unpack"),
                bind_next,
            )

        return OLet([(source_name, compiled_e)], compile_element(0, source_name, body))

    def visit_DestructuringAssign(self, node: TypedDestructuringAssign) -> CallAST:
        assert isinstance(
            node.value.typ, InstanceType
        ), "Can only deconstruct instances"
        source_typ = node.value.typ.typ
        compiled_source = self.visit(node.value)
        destructure_target = TypedTuple(
            elts=node.targets,
            ctx=Load(),
            typ=InstanceType(RawTupleType(node.element_typs)),
        )
        return lambda body: self._bind_target_from_compiled_expr(
            destructure_target,
            source_typ,
            compiled_source,
            body,
        )

    def visit_BinOp(self, node: TypedBinOp) -> plt.AST:
        try:
            op = node.left.typ.binop(node.op, node.right)
        except NotImplementedError as e:
            # try reverse binop
            try:
                op = node.right.typ.rbinop(node.op, node.left)
            except NotImplementedError:
                raise e
        return plt.Apply(
            op,
            self.visit(node.left),
            self.visit(node.right),
        )

    def visit_BoolOp(self, node: TypedBoolOp) -> plt.AST:
        assert len(node.values) >= 2, "Need to compare at least to values"

        def result_value(index: int, value: plt.AST) -> plt.AST:
            if needs_data_cast(node.typ):
                return transform_output_to_type(node.values[index].typ, node.typ)(value)
            return value

        def compile_value(index: int) -> plt.AST:
            value = node.values[index]
            if index == len(node.values) - 1:
                return result_value(index, self.visit(value))

            value_name = f"__boolop_value_{node.lineno}_{node.col_offset}_{index}"
            stored_value = OVar(value_name)
            truthy = plt.Not(
                plt.Apply(
                    value.typ.unop(ast.Not()),
                    stored_value,
                )
            )
            current_result = result_value(index, stored_value)
            if isinstance(node.op, ast.And):
                body = plt.Ite(truthy, compile_value(index + 1), current_result)
            else:
                body = plt.Ite(truthy, current_result, compile_value(index + 1))
            return OLet([(value_name, self.visit(value))], body)

        return compile_value(0)

    def visit_UnaryOp(self, node: TypedUnaryOp) -> plt.AST:
        op = node.operand.typ.unop(node.op)
        return plt.Apply(
            op,
            self.visit(node.operand),
        )

    def visit_Compare(self, node: TypedCompare) -> plt.AST:
        operands = [node.left] + node.comparators
        dunder_overrides = node.dunder_overrides
        operand_names = [
            f"__chain_cmp_value_{node.lineno}_{node.col_offset}_{i}"
            for i in range(len(operands))
        ]

        def compile_single_comparison(index: int) -> plt.AST:
            dunder_override = (
                dunder_overrides[index] if index < len(dunder_overrides) else None
            )
            if dunder_override is not None:
                dunder_function = TypedName(
                    id=dunder_override.method_name,
                    ctx=Load(),
                    typ=dunder_override.function_type,
                )
                dunder_function.orig_id = dunder_override.dunder_name
                arg_indices = (
                    [index + 1, index]
                    if dunder_override.receiver_right
                    else [index, index + 1]
                )
                dunder_call = TypedCall(
                    func=dunder_function,
                    args=[
                        RawPlutoExpr(
                            expr=OVar(operand_names[arg_index]),
                            typ=operands[arg_index].typ,
                        )
                        for arg_index in arg_indices
                    ],
                    keywords=[],
                    typ=BoolInstanceType,
                )
                dunder_call_result = self.visit_Call(dunder_call)
                if dunder_override.negate_result:
                    return plt.Not(dunder_call_result)
                return dunder_call_result
            op = operands[index].typ.cmp(node.ops[index], operands[index + 1].typ)
            return plt.Apply(
                op,
                OVar(operand_names[index]),
                OVar(operand_names[index + 1]),
            )

        def compile_chain(index: int) -> plt.AST:
            comparison_result = compile_single_comparison(index)
            if index == len(node.ops) - 1:
                return comparison_result
            return plt.Ite(
                comparison_result,
                OLet(
                    [
                        (
                            operand_names[index + 2],
                            self.visit(operands[index + 2]),
                        )
                    ],
                    compile_chain(index + 1),
                ),
                plt.Bool(False),
            )

        return OLet(
            [
                (operand_names[0], self.visit(operands[0])),
                (operand_names[1], self.visit(operands[1])),
            ],
            compile_chain(0),
        )

    def visit_Module(self, node: TypedModule) -> plt.AST:
        # extract actually read variables by each function
        if self.validator_function_name is not None:
            # for validators find main function
            # TODO can use more sophisiticated procedure here i.e. functions marked by comment
            main_fun: typing.Optional[InstanceType] = None
            for s in node.body:
                if (
                    isinstance(s, ast.FunctionDef)
                    and s.orig_name == self.validator_function_name
                ):
                    main_fun = s
            assert (
                main_fun is not None
            ), f"Could not find function named {self.validator_function_name}"
            main_fun_typ: FunctionType = main_fun.typ.typ
            assert isinstance(
                main_fun_typ, FunctionType
            ), f"Variable named {self.validator_function_name} is not of type function"

            body = node.body + (
                [
                    TypedReturn(
                        TypedCall(
                            func=ast.Name(
                                id=main_fun.name,
                                typ=InstanceType(main_fun_typ),
                                ctx=ast.Load(),
                            ),
                            typ=main_fun_typ.rettyp,
                            args=[
                                RawPlutoExpr(
                                    expr=(
                                        transform_ext_params_map(a)(
                                            OVar(f"val_param{i}")
                                        )
                                        if self.config.unwrap_input
                                        else OVar(f"val_param{i}")
                                    ),
                                    typ=a,
                                )
                                for i, a in enumerate(main_fun_typ.argtyps)
                            ],
                        )
                    ),
                ]
            )
            # TODO probably need to handle here when user wants to return something specific
            self.current_function_typ.append(
                FunctionType(
                    [],
                    InstanceType(
                        UnitType() if not self.config.wrap_output else AnyType()
                    ),
                )
            )
            name_load_visitor = NameLoadCollector()
            name_load_visitor.visit(node)
            all_vs = sorted(set(all_vars(node)) | set(name_load_visitor.loaded.keys()))

            # write all variables that are ever read
            # once at the beginning so that we can always access them (only potentially causing a nameerror at runtime)
            validator = SafeOLambda(
                [f"val_param{i}" for i, _ in enumerate(main_fun_typ.argtyps)],
                plt.Let(
                    [
                        (
                            x,
                            plt.Delay(
                                plt.TraceError(f"NameError: {map_to_orig_name(x)}")
                            ),
                        )
                        for x in all_vs
                    ],
                    self.visit_sequence(body)(plt.Unit()),
                ),
            )
            self.current_function_typ.pop()
        else:
            name_load_visitor = NameLoadCollector()
            name_load_visitor.visit(node)
            all_vs = sorted(set(all_vars(node)) | set(name_load_visitor.loaded.keys()))

            body = node.body
            # write all variables that are ever read
            # once at the beginning so that we can always access them (only potentially causing a nameerror at runtime)
            validator = plt.Let(
                [
                    (
                        x,
                        plt.Delay(plt.TraceError(f"NameError: {map_to_orig_name(x)}")),
                    )
                    for x in all_vs
                ],
                self.visit_sequence(body)(OUnit),
            )

        cp = plt.Program((1, 0, 0), validator)
        return cp

    def visit_Constant(self, node: Constant) -> plt.AST:
        if isinstance(node.value, bytes) and node.value != b"":
            try:
                bytes.fromhex(node.value.decode())
            except ValueError:
                pass
            else:
                OPSHIN_LOGGER.warning(
                    f"The string {node.value} looks like it is supposed to be a hex-encoded bytestring but is actually utf8-encoded. Try using `bytes.fromhex('{node.value.decode()}')` instead."
                )
        plt_val = plt.UPLCConstant(rec_constant_map(node.value))
        return plt_val

    def visit_NoneType(self, _: typing.Optional[typing.Any]) -> plt.AST:
        return plt.Unit()

    def visit_Assign(self, node: TypedAssign) -> CallAST:
        assert (
            len(node.targets) == 1
        ), "Assignments to more than one variable not supported yet"
        assert isinstance(
            node.targets[0], Name
        ), "Assignments to other things then names are not supported"
        compiled_e = self.visit(node.value)
        varname = node.targets[0].id
        if needs_data_cast(node.targets[0].typ):
            compiled_e = transform_output_to_type(node.value.typ, node.targets[0].typ)(
                compiled_e
            )
        # first evaluate the term, then wrap in a delay
        return lambda x: plt.Let(
            [
                (opshin_name_scheme_compatible_varname(varname), compiled_e),
                (varname, plt.Delay(OVar(varname))),
            ],
            x,
        )

    def visit_AnnAssign(self, node: TypedAnnAssign) -> CallAST:
        assert isinstance(
            node.target, Name
        ), "Assignments to other things then names are not supported"
        assert isinstance(
            node.target.typ, InstanceType
        ), "Can only assign instances to instances"
        val = self.visit(node.value)
        if isinstance(node.value.typ, InstanceType) and (
            isinstance(node.value.typ.typ, AnyType)
            or isinstance(node.value.typ.typ, UnionType)
        ):
            # we need to map this as it will originate from PlutusData
            # AnyType is the only type other than the builtin itself that can be cast to builtin values
            val = transform_ext_params_map(node.target.typ)(val)
        if needs_data_cast(node.target.typ):
            # we need to map this back as it will be treated as PlutusData
            # AnyType is the only type other than the builtin itself that can be cast to from builtin values
            val = transform_output_to_type(node.value.typ, node.target.typ)(val)
        return lambda x: plt.Let(
            [
                (opshin_name_scheme_compatible_varname(node.target.id), val),
                (node.target.id, plt.Delay(OVar(node.target.id))),
            ],
            x,
        )

    def visit_Name(self, node: Name) -> plt.AST:
        # depending on load or store context, return the value of the variable or its name
        if not isinstance(node.ctx, Load):
            raise NotImplementedError(f"Context {node.ctx} not supported")
        if isinstance(node.typ, ClassType):
            # if this is not an instance but a class, call the constructor
            return node.typ.constr()
        if isinstance(node.typ, DataInstanceType):
            return transform_ext_params_map(node.typ)(plt.Force(plt.Var(node.id)))
        return plt.Force(plt.Var(node.id))

    def visit_Expr(self, node: TypedExpr) -> CallAST:
        # we exploit UPLCs eager evaluation here
        # the expression is computed even though its value is eventually discarded
        # Note this really only makes sense for Trace
        # we use an invalid name here to avoid conflicts
        return lambda x: plt.Apply(OLambda(["0"], x), self.visit(node.value))

    def visit_Call(self, node: TypedCall) -> plt.AST:
        # compiled_args = " ".join(f"({self.visit(a)} {STATEMONAD})" for a in node.args)
        # return rf"(\{STATEMONAD} -> ({self.visit(node.func)} {compiled_args})"
        # TODO function is actually not of type polymorphic function type here anymore
        if isinstance(node.func.typ, PolymorphicFunctionInstanceType):
            # edge case for weird builtins that are polymorphic
            func_plt = force_params(
                node.func.typ.polymorphic_function.impl_from_args(
                    node.func.typ.typ.argtyps
                )
            )
            bind_self = None
        else:
            assert isinstance(node.func.typ, InstanceType) and isinstance(
                node.func.typ.typ, FunctionType
            ), "Can only call instances of functions"
            func_plt = self.visit(node.func)
            bind_self = node.func.typ.typ.bind_self
        bound_vs = sorted(list(node.func.typ.typ.bound_vars.keys()))
        args = []
        for i, (a, t) in enumerate(zip(node.args, node.func.typ.typ.argtyps)):
            # now impl_from_args has been chosen, skip type arg
            if (
                hasattr(node.func, "orig_id")
                and node.func.orig_id == "isinstance"
                and i == 1
            ):
                continue
            assert isinstance(t, InstanceType)
            # pass in all arguments evaluated with the statemonad
            a_int = self.visit(a)
            if needs_data_cast(t):
                # if the function expects input of generic type data, wrap data before passing it inside
                a_int = transform_output_to_type(a.typ, t)(a_int)
            args.append(a_int)
        # First assign to let to ensure that the arguments are evaluated before the call, but need to delay
        # as this is a variable assignment
        # Also bring all states of variables read inside the function into scope / update with value in current state
        # before call to simulate statemonad with current state being passed in
        return OLet(
            [(f"p{i}", a) for i, a in enumerate(args)],
            SafeApply(
                func_plt,
                *([plt.Var(bind_self)] if bind_self is not None else []),
                *[plt.Var(n) for n in bound_vs],
                *[plt.Delay(OVar(f"p{i}")) for i in range(len(args))],
            ),
        )

    def visit_FunctionDef(self, node: TypedFunctionDef) -> CallAST:
        body = node.body.copy()
        # defaults to returning None if there is no return statement
        if node.typ.typ.rettyp.typ == AnyType():
            ret_val = OUnit
        else:
            ret_val = plt.Unit()
        read_vs = sorted(list(node.typ.typ.bound_vars.keys()))
        if node.typ.typ.bind_self is not None:
            read_vs.insert(0, node.typ.typ.bind_self)
        self.current_function_typ.append(node.typ.typ)
        compiled_body = self.visit_sequence(body)(ret_val)
        self.current_function_typ.pop()
        return lambda x: plt.Let(
            [
                (
                    node.name,
                    plt.Delay(
                        SafeLambda(
                            read_vs + [a.arg for a in node.args.args],
                            compiled_body,
                        )
                    ),
                )
            ],
            x,
        )

    def visit_While(self, node: TypedWhile) -> CallAST:
        # the while loop calls itself, updating the values at overwritten names
        # by overwriting them with arguments to its self-recall
        if node.orelse:
            # If there is orelse, transform it to an appended sequence (TODO check if this is correct)
            cn = copy.copy(node)
            cn.orelse = []
            return self.visit_sequence([cn] + node.orelse)
        compiled_c = self.visit(node.test)
        compiled_s = self.visit_sequence(node.body)
        written_vs = written_vars(node)
        pwritten_vs = [plt.Var(x) for x in written_vs]
        s_fun = lambda x: plt.Lambda(
            [opshin_name_scheme_compatible_varname("while")] + written_vs,
            plt.Ite(
                compiled_c,
                compiled_s(
                    plt.Apply(
                        OVar("while"),
                        OVar("while"),
                        *copy.deepcopy(pwritten_vs),
                    )
                ),
                x,
            ),
        )

        return lambda x: OLet(
            [
                ("adjusted_next", SafeLambda(written_vs, x)),
                (
                    "while",
                    s_fun(
                        SafeApply(OVar("adjusted_next"), *copy.deepcopy(pwritten_vs))
                    ),
                ),
            ],
            plt.Apply(OVar("while"), OVar("while"), *copy.deepcopy(pwritten_vs)),
        )

    def visit_For(self, node: TypedFor) -> CallAST:
        if node.orelse:
            # If there is orelse, transform it to an appended sequence (TODO check if this is correct)
            cn = copy.copy(node)
            cn.orelse = []
            return self.visit_sequence([cn] + node.orelse)
        assert isinstance(node.iter.typ, InstanceType)
        if isinstance(node.iter.typ.typ, ListType):
            assert isinstance(
                node.target, Name
            ), "Can only assign value to singleton element"
            compiled_s = self.visit_sequence(node.body)
            compiled_iter = self.visit(node.iter)
            written_vs = written_vars(node)
            pwritten_vs = [plt.Var(x) for x in written_vs]
            s_fun = lambda x: plt.Lambda(
                [
                    opshin_name_scheme_compatible_varname("for"),
                    opshin_name_scheme_compatible_varname("iter"),
                ]
                + written_vs,
                plt.IteNullList(
                    OVar("iter"),
                    x,
                    plt.Let(
                        [(node.target.id, plt.Delay(plt.HeadList(OVar("iter"))))],
                        compiled_s(
                            plt.Apply(
                                OVar("for"),
                                OVar("for"),
                                plt.TailList(OVar("iter")),
                                *copy.deepcopy(pwritten_vs),
                            )
                        ),
                    ),
                ),
            )
            return lambda x: OLet(
                [
                    ("adjusted_next", plt.Lambda([node.target.id] + written_vs, x)),
                    (
                        "for",
                        s_fun(
                            plt.Apply(
                                OVar("adjusted_next"),
                                plt.Var(node.target.id),
                                *copy.deepcopy(pwritten_vs),
                            )
                        ),
                    ),
                ],
                plt.Apply(
                    OVar("for"),
                    OVar("for"),
                    compiled_iter,
                    *copy.deepcopy(pwritten_vs),
                ),
            )
        raise NotImplementedError(
            "Compilation of for statements for anything but lists not implemented yet"
        )

    def visit_If(self, node: TypedIf) -> CallAST:
        written_vs = written_vars(node)
        pwritten_vs = [plt.Var(x) for x in written_vs]
        return lambda x: OLet(
            [("adjusted_next", SafeLambda(written_vs, x))],
            plt.Ite(
                self.visit(node.test),
                self.visit_sequence(node.body)(
                    SafeApply(OVar("adjusted_next"), *copy.deepcopy(pwritten_vs))
                ),
                self.visit_sequence(node.orelse)(
                    SafeApply(OVar("adjusted_next"), *copy.deepcopy(pwritten_vs))
                ),
            ),
        )

    def visit_Return(self, node: TypedReturn) -> CallAST:
        value_plt = self.visit(node.value)
        assert self.current_function_typ, "Can not handle Return outside of a function"
        if needs_data_cast(self.current_function_typ[-1].rettyp):
            value_plt = transform_output_to_type(
                node.value.typ, self.current_function_typ[-1].rettyp
            )(value_plt)
        return lambda _: value_plt

    def _compile_list_slice(self, node: TypedSubscript) -> plt.AST:
        assert isinstance(node.slice, Slice)
        assert isinstance(node.value.typ.typ, ListType)
        assert node.slice.step is not None
        empty = empty_list(node.value.typ.typ.typ)
        bindings = [("slice_value", self.visit(node.value))]
        if node.slice.lower is not None:
            bindings.append(("raw_slice_start", self.visit(node.slice.lower)))
        if node.slice.upper is not None:
            bindings.append(("raw_slice_stop", self.visit(node.slice.upper)))
        if node.slice.step is not None:
            bindings.append(("slice_step", self.visit(node.slice.step)))

        positive_start = (
            plt.Integer(0)
            if node.slice.lower is None
            else _normalize_forward_slice_index(
                OVar("raw_slice_start"),
                plt.LengthList(OVar("slice_value")),
            )
        )
        positive_stop = (
            plt.LengthList(OVar("slice_value"))
            if node.slice.upper is None
            else _normalize_forward_slice_index(
                OVar("raw_slice_stop"),
                plt.LengthList(OVar("slice_value")),
            )
        )
        positive_slice = OLet(
            [("slice_start", positive_start), ("slice_stop", positive_stop)],
            plt.Ite(
                plt.EqualsInteger(OVar("slice_step"), plt.Integer(1)),
                _slice_list_contiguous(
                    OVar("slice_value"),
                    OVar("slice_start"),
                    OVar("slice_stop"),
                    empty,
                ),
                _slice_list_positive_stride(
                    OVar("slice_value"),
                    OVar("slice_start"),
                    OVar("slice_stop"),
                    OVar("slice_step"),
                    empty,
                ),
            ),
        )

        negative_limit = plt.SubtractInteger(OVar("slice_length"), plt.Integer(1))
        negative_start = (
            negative_limit
            if node.slice.lower is None
            else _normalize_slice_index(
                OVar("raw_slice_start"),
                OVar("slice_length"),
                plt.Integer(-1),
                negative_limit,
            )
        )
        negative_stop = (
            plt.Integer(-1)
            if node.slice.upper is None
            else _normalize_slice_index(
                OVar("raw_slice_stop"),
                OVar("slice_length"),
                plt.Integer(-1),
                negative_limit,
            )
        )
        negative_slice = OLet(
            [("slice_length", plt.LengthList(OVar("slice_value")))],
            OLet(
                [("slice_start", negative_start), ("slice_stop", negative_stop)],
                plt.Ite(
                    plt.LessThanInteger(OVar("slice_stop"), OVar("slice_start")),
                    OLet(
                        [
                            (
                                "reversed_slice_value",
                                _reverse_list(OVar("slice_value"), empty),
                            ),
                            (
                                "reversed_slice_start",
                                plt.SubtractInteger(
                                    negative_limit, OVar("slice_start")
                                ),
                            ),
                            (
                                "reversed_slice_stop",
                                plt.SubtractInteger(negative_limit, OVar("slice_stop")),
                            ),
                        ],
                        _slice_list_positive_stride(
                            OVar("reversed_slice_value"),
                            OVar("reversed_slice_start"),
                            OVar("reversed_slice_stop"),
                            plt.SubtractInteger(plt.Integer(0), OVar("slice_step")),
                            empty,
                        ),
                    ),
                    empty,
                ),
            ),
        )
        return OLet(
            bindings,
            plt.Ite(
                plt.EqualsInteger(OVar("slice_step"), plt.Integer(0)),
                plt.TraceError("ValueError: slice step cannot be zero"),
                plt.Ite(
                    plt.LessThanInteger(OVar("slice_step"), plt.Integer(0)),
                    negative_slice,
                    positive_slice,
                ),
            ),
        )

    def _compile_bytes_slice(self, node: TypedSubscript) -> plt.AST:
        assert isinstance(node.slice, Slice)
        assert node.slice.step is not None
        bindings = [("slice_value", self.visit(node.value))]
        if node.slice.lower is not None:
            bindings.append(("raw_slice_start", self.visit(node.slice.lower)))
        if node.slice.upper is not None:
            bindings.append(("raw_slice_stop", self.visit(node.slice.upper)))
        if node.slice.step is not None:
            bindings.append(("slice_step", self.visit(node.slice.step)))

        positive_start = (
            plt.Integer(0)
            if node.slice.lower is None
            else _normalize_slice_index(
                OVar("raw_slice_start"),
                OVar("slice_length"),
                plt.Integer(0),
                OVar("slice_length"),
            )
        )
        positive_stop = (
            OVar("slice_length")
            if node.slice.upper is None
            else _normalize_slice_index(
                OVar("raw_slice_stop"),
                OVar("slice_length"),
                plt.Integer(0),
                OVar("slice_length"),
            )
        )
        positive_slice = OLet(
            [("slice_length", plt.LengthOfByteString(OVar("slice_value")))],
            OLet(
                [("slice_start", positive_start), ("slice_stop", positive_stop)],
                plt.Ite(
                    plt.EqualsInteger(OVar("slice_step"), plt.Integer(1)),
                    _slice_bytes_contiguous(
                        OVar("slice_value"),
                        OVar("slice_start"),
                        OVar("slice_stop"),
                    ),
                    _slice_bytes_stride(
                        OVar("slice_value"),
                        OVar("slice_start"),
                        OVar("slice_stop"),
                        OVar("slice_step"),
                        True,
                    ),
                ),
            ),
        )

        negative_limit = plt.SubtractInteger(OVar("slice_length"), plt.Integer(1))
        negative_start = (
            negative_limit
            if node.slice.lower is None
            else _normalize_slice_index(
                OVar("raw_slice_start"),
                OVar("slice_length"),
                plt.Integer(-1),
                negative_limit,
            )
        )
        negative_stop = (
            plt.Integer(-1)
            if node.slice.upper is None
            else _normalize_slice_index(
                OVar("raw_slice_stop"),
                OVar("slice_length"),
                plt.Integer(-1),
                negative_limit,
            )
        )
        negative_slice = OLet(
            [("slice_length", plt.LengthOfByteString(OVar("slice_value")))],
            OLet(
                [("slice_start", negative_start), ("slice_stop", negative_stop)],
                _slice_bytes_stride(
                    OVar("slice_value"),
                    OVar("slice_start"),
                    OVar("slice_stop"),
                    OVar("slice_step"),
                    False,
                ),
            ),
        )
        return OLet(
            bindings,
            plt.Ite(
                plt.EqualsInteger(OVar("slice_step"), plt.Integer(0)),
                plt.TraceError("ValueError: slice step cannot be zero"),
                plt.Ite(
                    plt.LessThanInteger(OVar("slice_step"), plt.Integer(0)),
                    negative_slice,
                    positive_slice,
                ),
            ),
        )

    def visit_Subscript(self, node: TypedSubscript) -> plt.AST:
        assert isinstance(
            node.value.typ, InstanceType
        ), "Can only access elements of instances, not classes"
        if isinstance(node.value.typ.typ, RawTupleType):
            assert isinstance(
                node.slice, Constant
            ), "Only constant index access for tuples is supported"
            assert isinstance(
                node.slice.value, int
            ), "Only constant index integer access for tuples is supported"
            index = node.slice.value
            if index < 0:
                index += len(node.value.typ.typ.typs)
            assert isinstance(node.ctx, Load), "Tuples are read-only"
            return transform_ext_params_map(node.typ)(
                plt.ConstantIndexAccessListFast(
                    self.visit(node.value),
                    index,
                )
            )
        if isinstance(node.value.typ.typ, TupleType):
            assert isinstance(
                node.slice, Constant
            ), "Only constant index access for tuples is supported"
            assert isinstance(
                node.slice.value, int
            ), "Only constant index integer access for tuples is supported"
            index = node.slice.value
            if index < 0:
                index += len(node.value.typ.typ.typs)
            assert isinstance(node.ctx, Load), "Tuples are read-only"
            return plt.FunctionalTupleAccess(
                self.visit(node.value),
                index,
                len(node.value.typ.typ.typs),
            )
        if isinstance(node.value.typ.typ, PairType):
            assert isinstance(
                node.slice, Constant
            ), "Only constant index access for pairs is supported"
            assert isinstance(
                node.slice.value, int
            ), "Only constant index integer access for pairs is supported"
            index = node.slice.value
            if index < 0:
                index += 2
            assert isinstance(node.ctx, Load), "Pairs are read-only"
            assert (
                0 <= index < 2
            ), f"Pairs only have 2 elements, index should be -2, -1, 0 or 1, found {node.slice.value}"
            member_func = plt.FstPair if index == 0 else plt.SndPair
            # the content of pairs is always Data, so we need to unwrap
            member_typ = node.typ
            return transform_ext_params_map(member_typ)(
                member_func(
                    self.visit(node.value),
                ),
            )
        if isinstance(node.value.typ.typ, ListType):
            if not isinstance(node.slice, Slice):
                assert (
                    node.slice.typ == IntegerInstanceType
                ), "Only single element list index access supported"
                if isinstance(node.slice, Constant) and node.slice.value >= 0:
                    index = node.slice.value
                    return plt.ConstantIndexAccessListFast(
                        self.visit(node.value),
                        index,
                    )
                return OLet(
                    [
                        (
                            "l",
                            self.visit(node.value),
                        ),
                        (
                            "raw_i",
                            self.visit(node.slice),
                        ),
                        (
                            "i",
                            plt.Ite(
                                plt.LessThanInteger(OVar("raw_i"), plt.Integer(0)),
                                plt.AddInteger(
                                    OVar("raw_i"), plt.LengthList(OVar("l"))
                                ),
                                OVar("raw_i"),
                            ),
                        ),
                    ],
                    (
                        plt.IndexAccessListFast(self.config.fast_access_skip)(
                            OVar("l"), OVar("i")
                        )
                        if self.config.fast_access_skip is not None
                        else plt.IndexAccessList(OVar("l"), OVar("i"))
                    ),
                )
            else:
                if node.slice.step is not None:
                    return self._compile_list_slice(node)
                assert (
                    node.slice.upper is not None
                ), "Only slices with upper bound supported"
                assert (
                    node.slice.lower is not None
                ), "Only slices with lower bound supported"
                return OLet(
                    [
                        ("xs", self.visit(node.value)),
                        ("raw_i", self.visit(node.slice.lower)),
                        (
                            "i",
                            plt.Ite(
                                plt.LessThanInteger(OVar("raw_i"), plt.Integer(0)),
                                plt.AddInteger(
                                    OVar("raw_i"), plt.LengthList(OVar("xs"))
                                ),
                                OVar("raw_i"),
                            ),
                        ),
                        ("raw_j", self.visit(node.slice.upper)),
                        (
                            "j",
                            plt.Ite(
                                plt.LessThanInteger(OVar("raw_j"), plt.Integer(0)),
                                plt.AddInteger(
                                    OVar("raw_j"), plt.LengthList(OVar("xs"))
                                ),
                                OVar("raw_j"),
                            ),
                        ),
                        (
                            "drop",
                            plt.Ite(
                                plt.LessThanEqualsInteger(OVar("i"), plt.Integer(0)),
                                plt.Integer(0),
                                OVar("i"),
                            ),
                        ),
                        ("take", plt.SubtractInteger(OVar("j"), OVar("drop"))),
                    ],
                    plt.Ite(
                        plt.LessThanEqualsInteger(OVar("j"), OVar("i")),
                        empty_list(node.value.typ.typ.typ),
                        plt.SliceList(
                            OVar("drop"),
                            OVar("take"),
                            OVar("xs"),
                            empty_list(node.value.typ.typ.typ),
                        ),
                    ),
                )
        elif isinstance(node.value.typ.typ, DictType):
            dict_typ = node.value.typ.typ
            if not isinstance(node.slice, Slice):
                return OLet(
                    [
                        (
                            "key",
                            transform_output_map(node.slice.typ)(
                                self.visit(node.slice),
                            ),
                        )
                    ],
                    transform_ext_params_map(dict_typ.value_typ)(
                        plt.SndPair(
                            plt.FindList(
                                self.visit(node.value),
                                OLambda(
                                    ["x"],
                                    plt.EqualsData(
                                        OVar("key"),
                                        plt.FstPair(OVar("x")),
                                    ),
                                ),
                                plt.TraceError("KeyError"),
                            )
                        ),
                    ),
                )
        elif isinstance(node.value.typ.typ, ByteStringType):
            if not isinstance(node.slice, Slice):
                if isinstance(node.slice, Constant) and node.slice.value >= 0:
                    return plt.IndexByteString(
                        self.visit(node.value),
                        self.visit(node.slice),
                    )
                elif isinstance(node.slice, Constant) and node.slice.value < 0:
                    return plt.IndexByteString(
                        self.visit(node.value),
                        plt.AddInteger(
                            self.visit(node.slice),
                            plt.LengthOfByteString(self.visit(node.value)),
                        ),
                    )
                return OLet(
                    [
                        (
                            "bs",
                            self.visit(node.value),
                        ),
                        (
                            "raw_ix",
                            self.visit(node.slice),
                        ),
                        (
                            "ix",
                            plt.Ite(
                                plt.LessThanInteger(OVar("raw_ix"), plt.Integer(0)),
                                plt.AddInteger(
                                    OVar("raw_ix"),
                                    plt.LengthOfByteString(OVar("bs")),
                                ),
                                OVar("raw_ix"),
                            ),
                        ),
                    ],
                    plt.IndexByteString(OVar("bs"), OVar("ix")),
                )
            elif isinstance(node.slice, Slice):
                if node.slice.step is not None:
                    return self._compile_bytes_slice(node)
                return OLet(
                    [
                        ("bs", self.visit(node.value)),
                        ("raw_i", self.visit(node.slice.lower)),
                        (
                            "i",
                            plt.Ite(
                                plt.LessThanInteger(OVar("raw_i"), plt.Integer(0)),
                                plt.AddInteger(
                                    OVar("raw_i"),
                                    plt.LengthOfByteString(OVar("bs")),
                                ),
                                OVar("raw_i"),
                            ),
                        ),
                        ("raw_j", self.visit(node.slice.upper)),
                        (
                            "j",
                            plt.Ite(
                                plt.LessThanInteger(OVar("raw_j"), plt.Integer(0)),
                                plt.AddInteger(
                                    OVar("raw_j"),
                                    plt.LengthOfByteString(OVar("bs")),
                                ),
                                OVar("raw_j"),
                            ),
                        ),
                        (
                            "drop",
                            plt.Ite(
                                plt.LessThanEqualsInteger(OVar("i"), plt.Integer(0)),
                                plt.Integer(0),
                                OVar("i"),
                            ),
                        ),
                        ("take", plt.SubtractInteger(OVar("j"), OVar("drop"))),
                    ],
                    plt.Ite(
                        plt.LessThanEqualsInteger(OVar("j"), OVar("i")),
                        plt.ByteString(b""),
                        plt.SliceByteString(
                            OVar("drop"),
                            OVar("take"),
                            OVar("bs"),
                        ),
                    ),
                )
        raise NotImplementedError(
            f'Could not implement subscript "{node.slice}" of "{node.value}"'
        )

    def visit_Tuple(self, node: TypedTuple) -> plt.AST:
        assert isinstance(node.typ, InstanceType)
        if isinstance(node.typ.typ, RawTupleType):
            tuple_value = plt.EmptyDataList()
            for e in reversed(node.elts):
                tuple_value = plt.MkCons(
                    transform_output_map(e.typ)(self.visit(e)),
                    tuple_value,
                )
            return tuple_value
        return plt.FunctionalTuple(*(self.visit(e) for e in node.elts))

    def visit_ClassDef(self, node: TypedClassDef) -> CallAST:
        return lambda x: plt.Let([(node.name, plt.Delay(node.class_typ.constr()))], x)

    def visit_Attribute(self, node: TypedAttribute) -> plt.AST:
        assert isinstance(
            node.value.typ, InstanceType
        ), "Can only access attributes of instances"
        obj = self.visit(node.value)
        attr = node.value.typ.attribute(node.attr)
        return plt.Apply(attr, obj)

    def visit_Assert(self, node: TypedAssert) -> CallAST:
        return lambda x: plt.Ite(
            self.visit(node.test),
            x,
            plt.Apply(
                plt.Error(),
                (
                    plt.Trace(self.visit(node.msg), plt.Unit())
                    if node.msg is not None
                    else plt.Unit()
                ),
            ),
        )

    def visit_RawPlutoExpr(self, node: RawPlutoExpr) -> plt.AST:
        return node.expr

    def visit_List(self, node: TypedList) -> plt.AST:
        assert isinstance(node.typ, InstanceType)
        assert isinstance(node.typ.typ, ListType)
        el_typ = node.typ.typ.typ
        l = empty_list(el_typ)
        for e in reversed(node.elts):
            element = self.visit(e)
            if isinstance(el_typ.typ, AnyType) or isinstance(el_typ.typ, UnionType):
                # if the function expects input of generic type data, wrap data before passing it inside
                element = transform_output_map(e.typ)(element)
            l = plt.MkCons(element, l)
        return l

    def visit_Dict(self, node: TypedDict) -> plt.AST:
        assert isinstance(node.typ, InstanceType)
        assert isinstance(node.typ.typ, DictType)
        items = plt.EmptyDataPairList()
        for k, v in reversed(list(zip(node.keys, node.values))):
            items = plt.MkCons(
                plt.MkPairData(
                    transform_output_map(k.typ)(
                        self.visit(k),
                    ),
                    transform_output_map(v.typ)(
                        self.visit(v),
                    ),
                ),
                items,
            )
        if self.config.dict_last_value_wins:
            return self._normalize_dict_items(items)
        return items

    @staticmethod
    def _normalize_dict_items(items: plt.AST) -> plt.AST:
        """Apply Python's ordered, last-value-wins dictionary insertion rules."""
        insert_name = "__dict_insert"
        insert = plt.RecFun(
            OLambda(
                ["insert", "items", "pair"],
                plt.IteNullList(
                    OVar("items"),
                    plt.MkCons(OVar("pair"), plt.EmptyDataPairList()),
                    OLet(
                        [
                            ("head", plt.HeadList(OVar("items"))),
                            ("tail", plt.TailList(OVar("items"))),
                        ],
                        plt.Ite(
                            plt.EqualsData(
                                plt.FstPair(OVar("head")),
                                plt.FstPair(OVar("pair")),
                            ),
                            plt.MkCons(OVar("pair"), OVar("tail")),
                            plt.MkCons(
                                OVar("head"),
                                plt.Apply(
                                    OVar("insert"),
                                    OVar("insert"),
                                    OVar("tail"),
                                    OVar("pair"),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        )
        return OLet(
            [(insert_name, insert)],
            plt.FoldList(
                items,
                OLambda(
                    ["result", "pair"],
                    plt.Apply(
                        OVar(insert_name),
                        OVar("result"),
                        OVar("pair"),
                    ),
                ),
                plt.EmptyDataPairList(),
            ),
        )

    def visit_IfExp(self, node: TypedIfExp) -> plt.AST:
        if isinstance(node.typ.typ, UnionType):
            body = self.visit(node.body)
            orelse = self.visit(node.orelse)
            if not isinstance(node.body.typ, UnionType):
                body = transform_output_map(node.body.typ)(body)
            if not isinstance(node.orelse.typ, UnionType):
                orelse = transform_output_map(node.orelse.typ)(orelse)
            return plt.Ite(self.visit(node.test), body, orelse)
        return plt.Ite(
            self.visit(node.test),
            self.visit(node.body),
            self.visit(node.orelse),
        )

    def visit_ListComp(self, node: TypedListComp) -> plt.AST:
        assert len(node.generators) == 1, "Currently only one generator supported"
        gen = node.generators[0]
        assert isinstance(gen.iter.typ, InstanceType), "Only lists are valid generators"
        assert isinstance(gen.iter.typ.typ, ListType), "Only lists are valid generators"
        source_typ = gen.iter.typ.typ.typ
        lst = self.visit(gen.iter)
        ifs = None
        for ifexpr in gen.ifs:
            if ifs is None:
                ifs = self.visit(ifexpr)
            else:
                ifs = plt.And(ifs, self.visit(ifexpr))
        map_fun = OLambda(
            ["x"],
            self._bind_target_from_compiled_expr(
                gen.target,
                source_typ,
                OVar("x"),
                self.visit(node.elt),
            ),
        )
        empty_list_con = empty_list(node.elt.typ)
        if ifs is not None:
            filter_fun = OLambda(
                ["x"],
                self._bind_target_from_compiled_expr(
                    gen.target,
                    source_typ,
                    OVar("x"),
                    ifs,
                ),
            )
            result = plt.MapFilterList(
                lst,
                filter_fun,
                map_fun,
                empty_list_con,
            )
        else:
            result = plt.MapList(
                lst,
                map_fun,
                empty_list_con,
            )
        return result

    def visit_DictComp(self, node: TypedDictComp) -> plt.AST:
        assert len(node.generators) == 1, "Currently only one generator supported"
        gen = node.generators[0]
        assert isinstance(gen.iter.typ, InstanceType), "Only lists are valid generators"
        assert isinstance(gen.iter.typ.typ, ListType), "Only lists are valid generators"
        source_typ = gen.iter.typ.typ.typ
        lst = self.visit(gen.iter)
        ifs = None
        for ifexpr in gen.ifs:
            if ifs is None:
                ifs = self.visit(ifexpr)
            else:
                ifs = plt.And(ifs, self.visit(ifexpr))
        map_fun = OLambda(
            ["x"],
            self._bind_target_from_compiled_expr(
                gen.target,
                source_typ,
                OVar("x"),
                plt.MkPairData(
                    transform_output_map(node.key.typ)(
                        self.visit(node.key),
                    ),
                    transform_output_map(node.value.typ)(
                        self.visit(node.value),
                    ),
                ),
            ),
        )
        empty_list_con = plt.EmptyDataPairList()
        if ifs is not None:
            filter_fun = OLambda(
                ["x"],
                self._bind_target_from_compiled_expr(
                    gen.target,
                    source_typ,
                    OVar("x"),
                    ifs,
                ),
            )
            result = plt.MapFilterList(
                lst,
                filter_fun,
                map_fun,
                empty_list_con,
            )
        else:
            result = plt.MapList(
                lst,
                map_fun,
                empty_list_con,
            )
        if self.config.dict_last_value_wins:
            return self._normalize_dict_items(result)
        return result

    def visit_FormattedValue(self, node: TypedFormattedValue) -> plt.AST:
        return plt.Apply(
            node.value.typ.stringify(),
            self.visit(node.value),
        )

    def visit_JoinedStr(self, node: TypedJoinedStr) -> plt.AST:
        joined_str = plt.Text("")
        for v in reversed(node.values):
            joined_str = plt.AppendString(self.visit(v), joined_str)
        return joined_str

    def generic_visit(self, node: TypedAST) -> plt.AST:
        raise NotImplementedError(f"Can not compile {node}")


_OPTIMIZATION_HINT_RE = re.compile(
    r"#\s*opshin:\s*(branch-probability|iterations)\s*=\s*" r"(\S+)\s*$"
)


def _annotate_optimization_hints(tree: ast.AST, source: str) -> None:
    compound_statements = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.If, ast.For, ast.While))
    ]
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        match = _OPTIMIZATION_HINT_RE.fullmatch(token.string)
        if match is None:
            continue
        hint, raw_value = match.groups()
        line = token.start[0]
        candidates = []
        for node in compound_statements:
            first_body_line = min(
                (statement.lineno for statement in node.body),
                default=getattr(node, "end_lineno", node.lineno) + 1,
            )
            if node.lineno <= line < first_body_line:
                candidates.append(node)
        assert (
            candidates
        ), f"Optimization hint on line {line} is not on a compound statement header"
        node = max(candidates, key=lambda candidate: candidate.lineno)
        value = float(raw_value)
        assert math.isfinite(value), f"Optimization hint on line {line} must be finite"
        if hint == "branch-probability":
            assert isinstance(
                node, ast.If
            ), f"branch-probability hint on line {line} is only valid on if statements"
            assert (
                0.0 <= value <= 1.0
            ), f"branch-probability on line {line} must be between 0 and 1"
            node.branch_probability = value
        else:
            assert isinstance(
                node, (ast.For, ast.While)
            ), f"iterations hint on line {line} is only valid on loops"
            assert value >= 0.0, f"iterations on line {line} must be non-negative"
            node.iterations = value


def parse(
    source: str,
    filename=None,
) -> ast.AST:
    """
    Parse source code into an AST

    Besides parsing Python, this attaches selective-narrowing cost hints from
    comments on compound statement headers. ``branch-probability`` gives the
    probability that an ``if`` condition is true, while ``iterations`` gives
    the expected number of loop-body executions.
    """
    tree = ast.parse(source, filename=filename)
    _annotate_optimization_hints(tree, source)
    return tree


def compile(
    prog: ast.AST,
    filename=None,
    validator_function_name="validator",
    config=DEFAULT_CONFIG,
    wrap_output=False,
    validator_signature: typing.Optional[typing.List[ValidatorSignature]] = None,
) -> plt.Program:
    if not __debug__:
        raise RuntimeError(
            "opshin compilation requires Python assertions; do not run Python with -O"
        )
    compile_pipeline = [
        # Important to call this one first - it imports all further files
        RewriteImport(filename=filename),
        # Rewrites that simplify the python code
        RewriteForbiddenReturn(),
        OptimizeUnionExpansion() if config.expand_union_types else NoOp(),
        OptimizeConstantFolding() if config.constant_folding else NoOp(),
        RewriteSubscript38(),
        RewriteAugAssign(),
        RewriteTupleAssign(),
        RewriteImportBLS12381(),
        RewriteImportIntegrityCheck(),
        RewriteImportPlutusData(),
        RewriteImportHashlib(),
        RewriteImportTyping(),
        RewriteForbiddenOverwrites(),
        RewriteImportDataclasses(),
        RewriteInjectBuiltins(),
        RewriteConditions(),
        # Save the original names of variables
        RewriteOrigName(),
        RewriteScoping(),
        RewriteAnnotateFallthrough(),
        # The type inference needs to be run after complex python operations were rewritten
        AggressiveTypeInferencer(config.allow_isinstance_anything),
        AnalyzeIntegrity(validator_function_name),
        (
            OptimizeRemoveCheckedIntegrityChecks()
            if config.optimize_remove_checked_integrity_checks
            else NoOp()
        ),
        (
            OptimizeSelectiveNarrowing(config.allow_isinstance_anything)
            if config.optimize_selective_narrowing
            else NoOp()
        ),
        RewriteDestructuringAssign(),
        (RewriteExpandedUnionCalls() if config.expand_union_types else NoOp()),
        RewriteFunctionClosures(),
        # Rewrites that circumvent the type inference or use its results
        OptimizeBoolOnlyOps() if config.optimize_bool_only_ops else NoOp(),
        OptimizeFoldBoolCast(),
        RewriteAssertNone(),
        RewriteEmptyLists(),
        RewriteEmptyDicts(),
        RewriteImportUPLCBuiltins(),
        RewriteRemoveTypeStuff(),
    ]
    for s in compile_pipeline:
        prog = s.visit(prog)
        prog = custom_fix_missing_locations(prog)
        if isinstance(s, AggressiveTypeInferencer) and validator_signature is not None:
            validator_signature.append(
                _extract_validator_signature(prog, validator_function_name)
            )

    # Apply optimizations repeatedly until no further changes occur (fixed-point)
    optimize_pipeline = [
        OptimizeRemoveTrace() if config.remove_trace else NoOp(),
        OptimizeFoldIfFallthrough() if config.remove_dead_code else NoOp(),
        OptimizeRemoveUnreachable() if config.remove_dead_code else NoOp(),
        RewriteAdjacentInline() if config.adjacent_inline else NoOp(),
        (
            OptimizeRemoveDeadvars(validator_function_name=validator_function_name)
            if config.remove_dead_code
            else NoOp()
        ),
        OptimizeRemoveDeadConstants() if config.remove_dead_code else NoOp(),
        OptimizeRemoveDeadConditions() if config.remove_dead_code else NoOp(),
        OptimizeRemovePass(),
    ]
    _MAX_OPTIMIZER_ITERATIONS = 100
    for _ in range(_MAX_OPTIMIZER_ITERATIONS):
        prog_dump = ast.dump(prog)
        for s in optimize_pipeline:
            prog = s.visit(prog)
            prog = custom_fix_missing_locations(prog)
        if ast.dump(prog) == prog_dump:
            break
    else:
        raise RuntimeError(
            f"Optimizer did not reach a fixed point after {_MAX_OPTIMIZER_ITERATIONS} iterations. "
            "This is likely a bug in one of the optimizer steps."
        )

    # the compiler runs last
    s = PlutoCompiler(
        validator_function_name=validator_function_name,
        config=config,
    )
    prog = s.visit(prog)

    return prog
