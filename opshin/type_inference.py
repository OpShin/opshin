"""
An aggressive type inference based on the work of Aycock [1].
It only allows a subset of legal python operations which
allow us to infer the type of all involved variables
statically.
Using this we can resolve overloaded functions when translating Python
into UPLC where there is no dynamic type checking.
Additionally, this conveniently implements an additional layer of
security into the Smart Contract by checking type correctness.


[1]: https://legacy.python.org/workshops/2000-01/proceedings/papers/aycock/aycock.html
"""

import re
import ast
from ast import *
import typing
from collections import defaultdict
from copy import copy
from hashlib import sha256

from frozenlist2 import frozenlist
from ordered_set import OrderedSet
from pycardano import PlutusData
from typing import Union
import pluthon as plt
from .typed_ast import *
from .util import (
    CompilingNodeTransformer,
    distinct,
    TypedNodeVisitor,
    OPSHIN_LOGGER,
    custom_fix_missing_locations,
    read_vars,
    externally_bound_vars,
)
from .fun_impls import PythonBuiltInTypes
from .rewrite.rewrite_cast_condition import SPECIAL_BOOL
from .type_impls import (
    Type,
    ByteStringType,
    IntegerType,
    StringType,
    AnyType,
    BoolType,
    InstanceType,
    RecordType,
    PolymorphicFunctionType,
    Record,
    BoolInstanceType,
    IntegerInstanceType,
    UnitInstanceType,
    ByteStringInstanceType,
    StringInstanceType,
    ListType,
    DictType,
    UnionType,
    PairType,
    TypeInferenceError,
    UnitType,
    ATOMIC_TYPES,
    ClassType,
    TupleType,
    PolymorphicFunctionInstanceType,
    FunctionType,
)

# from frozendict import frozendict


INITIAL_SCOPE = {
    # class annotations
    "bytes": ByteStringType(),
    "bytearray": ByteStringType(),
    "int": IntegerType(),
    "bool": BoolType(),
    "str": StringType(),
    "Anything": AnyType(),
}

INITIAL_SCOPE.update(
    {
        name.name: typ
        for name, typ in PythonBuiltInTypes.items()
        if isinstance(typ.typ, PolymorphicFunctionType)
    }
)

DUNDER_MAP = {
    # ast.Compare:
    ast.Eq: "__eq__",
    ast.NotEq: "__ne__",
    ast.Lt: "__lt__",
    ast.LtE: "__le__",
    ast.Gt: "__gt__",
    ast.GtE: "__ge__",
    # ast.Is # no dunder
    # ast.IsNot # no dunder
    ast.In: "__contains__",
    ast.NotIn: "__contains__",
    # ast.Binop:
    ast.Add: "__add__",
    ast.Sub: "__sub__",
    ast.Mult: "__mul__",
    ast.Div: "__truediv__",
    ast.FloorDiv: "__floordiv__",
    ast.Mod: "__mod__",
    ast.Pow: "__pow__",
    ast.MatMult: "__matmul__",
    # ast.UnaryOp:
    # ast.UAdd
    ast.USub: "__neg__",
    ast.Not: "__bool__",
    ast.Invert: "__invert__",
    # ast.BoolOp
    ast.And: "__and__",
    ast.Or: "__or__",
}

DUNDER_REVERSE_MAP = {
    ast.Add: "__radd__",
    ast.Sub: "__rsub__",
    ast.Mult: "__rmul__",
    ast.Div: "__rtruediv__",
    ast.FloorDiv: "__rfloordiv__",
    ast.Mod: "__rmod__",
    ast.Pow: "__rpow__",
    ast.LShift: "__rlshift__",
    ast.RShift: "__rrshift__",
    ast.And: "__rand__",
    ast.Or: "__ror__",
}

ALL_DUNDERS = set(DUNDER_MAP.values()).union(set(DUNDER_REVERSE_MAP.values()))


def record_from_plutusdata(c: PlutusData):
    return Record(
        name=c.__class__.__name__,
        orig_name=c.__class__.__name__,
        constructor=c.CONSTR_ID,
        fields=frozenlist([(k, constant_type(v)) for k, v in c.__dict__.items()]),
    )


def constant_type(c):
    if isinstance(c, bool):
        return BoolInstanceType
    if isinstance(c, int):
        return IntegerInstanceType
    if isinstance(c, type(None)):
        return UnitInstanceType
    if isinstance(c, bytes):
        return ByteStringInstanceType
    if isinstance(c, str):
        return StringInstanceType
    if isinstance(c, list):
        assert len(c) > 0, "Lists must be non-empty"
        types = [constant_type(x) for x in c]
        first_typ = find_max_type([InstanceType(t) for t in types])
        if first_typ is None:
            raise ValueError(
                f"All elements in a list must have a compatible type, found typs {tuple(t.python_type() for t in types)}"
            )
        return InstanceType(ListType(first_typ))
    if isinstance(c, dict):
        assert len(c) > 0, "Dicts must be non-empty"

        key_types = [constant_type(k) for k in c.keys()]
        value_types = [constant_type(v) for v in c.values()]
        first_key_typ = find_max_type([InstanceType(t) for t in key_types])
        first_value_typ = find_max_type([InstanceType(t) for t in value_types])
        if first_key_typ is None:
            raise ValueError(
                f"All keys in a dict must have a compatible type, found typs {tuple(t.python_type() for t in key_types)}"
            )
        if first_value_typ is None:
            raise ValueError(
                f"All values in a dict must have a compatible type, found typs {tuple(t.python_type() for t in value_types)}"
            )
        return InstanceType(DictType(first_key_typ, first_value_typ))
    if isinstance(c, PlutusData):
        return InstanceType(RecordType(record=record_from_plutusdata(c)))
    raise NotImplementedError(f"Type {type(c)} not supported")


TypeMap = typing.Dict[str, Type]
TypeMapPair = typing.Tuple[TypeMap, TypeMap]


def union_types(*ts: Type):
    ts = OrderedSet(ts)
    # If all types are the same, just return the type
    if len(ts) == 1:
        return ts[0]
    # If there is a type that is compatible with all other types, choose the maximum
    for t in ts:
        if all(t >= tp for tp in ts):
            return t
    assert ts, "Union must combine multiple classes"
    # flatten encountered union types
    all_ts = []
    to_process = list(reversed(ts))
    while to_process:
        t = to_process.pop()
        if isinstance(t, UnionType):
            to_process = to_process.extend(reversed(t.typs))
        else:
            assert isinstance(
                t, (RecordType, IntegerType, ByteStringType, ListType, DictType)
            ), f"Union must combine multiple PlutusData, int, bytes, List[Anything] or Dict[Anything,Anything] but found {t.python_type()}"
            if isinstance(t, ListType):
                assert isinstance(t.typ, InstanceType) and isinstance(
                    t.typ.typ, AnyType
                ), "Union must contain only lists of Any, i.e. List[Anything]"
            if isinstance(t, DictType):
                assert (
                    isinstance(t.key_typ, InstanceType)
                    and isinstance(t.key_typ.typ, AnyType)
                    and isinstance(t.value_typ, InstanceType)
                    and isinstance(t.value_typ.typ, AnyType)
                ), "Union must contain only dicts of Any, i.e. Dict[Anything, Anything]"
            all_ts.append(t)
    union_set = OrderedSet(all_ts)
    assert distinct(
        [
            e.record.constructor
            for e in union_set
            if not isinstance(e, (ByteStringType, IntegerType, ListType, DictType))
        ]
    ), (
        "Union must combine PlutusData classes with unique CONSTR_ID, but found duplicates: "
        + str(
            {
                e.record.orig_name: e.record.constructor
                for e in union_set
                if isinstance(e, RecordType)
            }
        )
    )
    return UnionType(frozenlist(union_set))


def intersection_types(*ts: Type):
    ts = OrderedSet(ts)
    if len(ts) == 1:
        return ts[0]
    ts = [t if isinstance(t, UnionType) else UnionType(frozenlist([t])) for t in ts]
    assert ts, "Must have at least one type to intersect"
    intersection_set = OrderedSet(ts[0].typs)
    for t in ts[1:]:
        intersection_set.intersection_update(t.typs)
    return UnionType(frozenlist(intersection_set))


def find_max_type(elts: typing.List[InstanceType]):
    if not elts:
        return InstanceType(AnyType())
    set_elts = OrderedSet(elts)
    max_typ = None
    for m in elts:
        l_typ = m.typ
        if all(l_typ >= e.typ for e in set_elts):
            max_typ = l_typ
            break
    if max_typ is None:
        # try to derive a union type
        try:
            max_typ = InstanceType(union_types(*(e.typ.typ for e in set_elts)))
        except AssertionError:
            # if this fails, we have a list with incompatible types
            raise ValueError(
                f"All elements must have a compatible type, found typs {tuple(e.typ.python_type() for e in elts)}"
            )
    return max_typ


class TypeCheckVisitor(TypedNodeVisitor):
    """
    Generates the types to which objects are cast due to a boolean expression
    It returns a tuple of dictionaries which are a name -> type mapping
    for variable names that are assured to have a specific type if this expression
    is True/False respectively
    """

    def __init__(self, allow_isinstance_anything=False):
        self.allow_isinstance_anything = allow_isinstance_anything

    def generic_visit(self, node: AST) -> TypeMapPair:
        return getattr(node, "typechecks", ({}, {}))

    def visit_Call(self, node: Call) -> TypeMapPair:
        if isinstance(node.func, Name) and node.func.orig_id == SPECIAL_BOOL:
            return self.visit(node.args[0])
        if not (isinstance(node.func, Name) and node.func.orig_id == "isinstance"):
            return ({}, {})
        # special case for Union
        if not isinstance(node.args[0], Name):
            OPSHIN_LOGGER.warning(
                "Target 0 of an isinstance cast must be a variable name for type casting to work. You can still proceed, but the inferred type of the isinstance cast will not be accurate."
            )
            return ({}, {})
        assert isinstance(node.args[1], Name) or isinstance(
            node.args[1].typ, (ListType, DictType)
        ), "Target 1 of an isinstance cast must be a class name"
        target_class: RecordType = node.args[1].typ
        inst = node.args[0]
        inst_class = inst.typ
        assert isinstance(
            inst_class, InstanceType
        ), "Can only cast instances, not classes"
        # assert isinstance(target_class, RecordType), "Can only cast to PlutusData"
        if isinstance(inst_class.typ, UnionType):
            assert (
                target_class in inst_class.typ.typs
            ), f"Trying to cast an instance of Union type to non-instance of union type"
            union_without_target_class = union_types(
                *(x for x in inst_class.typ.typs if x != target_class)
            )
        elif isinstance(inst_class.typ, AnyType) and self.allow_isinstance_anything:
            union_without_target_class = AnyType()
        else:
            assert (
                inst_class.typ == target_class
            ), "Can only cast instances of Union types of PlutusData or cast the same class. If you know what you are doing, enable the flag '--allow-isinstance-anything'"
            union_without_target_class = target_class
        varname = node.args[0].id
        return ({varname: target_class}, {varname: union_without_target_class})

    def visit_BoolOp(self, node: BoolOp) -> TypeMapPair:
        res = {}
        inv_res = {}
        checks = [self.visit(v) for v in node.values]
        checked_types = defaultdict(list)
        inv_checked_types = defaultdict(list)
        for c, inv_c in checks:
            for v, t in c.items():
                checked_types[v].append(t)
            for v, t in inv_c.items():
                inv_checked_types[v].append(t)
        if isinstance(node.op, And):
            # a conjunction is just the intersection
            for v, ts in checked_types.items():
                res[v] = intersection_types(*ts)
            # if the conjunction fails, its any of the respective reverses, but only if the type is checked in every conjunction
            for v, ts in inv_checked_types.items():
                if len(ts) < len(checks):
                    continue
                inv_res[v] = union_types(*ts)
        elif isinstance(node.op, Or):
            # a disjunction is just the union, but some type must be checked in every disjunction
            for v, ts in checked_types.items():
                if len(ts) < len(checks):
                    continue
                res[v] = union_types(*ts)
            # if the disjunction fails, then it must be in the intersection of the inverses
            for v, ts in inv_checked_types.items():
                inv_res[v] = intersection_types(*ts)
        else:
            raise NotImplementedError(f"Unsupported boolean operator {node.op}")
        return (res, inv_res)

    def visit_UnaryOp(self, node: UnaryOp) -> TypeMapPair:
        (res, inv_res) = self.visit(node.operand)
        if isinstance(node.op, Not):
            return (inv_res, res)
        return (res, inv_res)


def merge_scope(s1: typing.Dict[str, Type], s2: typing.Dict[str, Type]):
    keys = OrderedSet(s1.keys()).union(s2.keys())
    merged = {}
    for k in keys:
        if k not in s1.keys():
            merged[k] = s2[k]
        elif k not in s2.keys():
            merged[k] = s1[k]
        else:
            try:
                assert isinstance(s1[k], InstanceType) and isinstance(
                    s2[k], InstanceType
                ), f"""Can only merge instance types, found class type '{s1[k].python_type() if not isinstance(s1[k], InstanceType) else s2[k].python_type() if not isinstance(s2[k], InstanceType) else s1[k].python_type() + "' and '" + s1[k].python_type()}' for '{k}'"""
                merged[k] = InstanceType(union_types(s1[k].typ, s2[k].typ))
            except AssertionError as e:
                raise AssertionError(
                    f"Can not merge scopes after branching, conflicting types for '{k}': '{e}'"
                )
    return merged


class AggressiveTypeInferencer(CompilingNodeTransformer):
    step = "Static Type Inference"

    def __init__(self, allow_isinstance_anything=False):
        self.allow_isinstance_anything = allow_isinstance_anything
        self.FUNCTION_ARGUMENT_REGISTRY = {}
        self.wrapped = []
        # Per-sequence metadata used to derive transitive closure environments for functions.
        self.function_bound_name_scopes: typing.List[
            typing.Dict[int, typing.Set[str]]
        ] = []
        self.first_function_definition_scopes: typing.List[typing.Set[int]] = []

        # A stack of dictionaries for storing scoped knowledge of variable types
        self.scopes = [INITIAL_SCOPE]

    # Obtain the type of a variable name in the current scope
    def variable_type(self, name: str) -> Type:
        name = name
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        # try to find an outer scope where the variable name maps to the original name
        outer_scope_type = None
        for scope in reversed(self.scopes):
            for key, type in scope.items():
                if map_to_orig_name(key) == map_to_orig_name(name):
                    outer_scope_type = type
        if outer_scope_type is None:
            # If the variable is not found in any scope, raise an error
            raise TypeInferenceError(
                f"Variable '{map_to_orig_name(name)}' not initialized at access. You need to define it before using it the first time."
            )
        else:
            raise TypeInferenceError(
                f"Variable '{map_to_orig_name(name)}' not initialized at access.\n"
                f"Note that you may be trying to access variable '{map_to_orig_name(name)}' of type '{outer_scope_type.python_type()}' in an outer scope and later redefine it. This is not allowed.\n"
                "This can happen for example if you redefine a (renamed) imported function but try to use it before the redefinition."
            )

    def is_defined_in_current_scope(self, name: str) -> bool:
        try:
            self.variable_type(name)
            return True
        except TypeInferenceError:
            return False

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def set_variable_type(self, name: str, typ: Type, force=False):
        if not force and name in self.scopes[-1] and self.scopes[-1][name] != typ:
            if self.scopes[-1][name] >= typ:
                # the specified type is broader, we pass on this
                return
            raise TypeInferenceError(
                f"Type '{self.scopes[-1][name].python_type()}' of variable '{map_to_orig_name(name)}' in local scope does not match inferred type '{typ.python_type()}'"
            )
        self.scopes[-1][name] = typ

    def implement_typechecks(self, typchecks: TypeMap):
        prevtyps = {}
        for n, t in typchecks.items():
            prevtyps[n] = self.variable_type(n).typ
            self.set_variable_type(n, InstanceType(t), force=True)
        return prevtyps

    def dunder_override(self, node: Union[BinOp, Compare, UnaryOp]):
        # Check for potential dunder_method override
        operand = None
        operation = None
        args = []
        if isinstance(node, UnaryOp):
            operand = self.visit(node.operand)
            operation = node.op
        elif isinstance(node, BinOp):
            operand = self.visit(node.left)
            operation = node.op
            args = [self.visit(node.right)]
        elif isinstance(node, Compare):
            operation = node.ops[0]
            if any([isinstance(operation, x) for x in [ast.In, ast.NotIn]]):
                operand = self.visit(node.comparators[0])
                args = [self.visit(node.left)]
            else:
                operand = self.visit(node.left)
                args = [self.visit(c) for c in node.comparators]
            assert len(node.ops) == 1, "Only support one op at a time"
        operand_type = operand.typ
        if (
            operation.__class__ in DUNDER_MAP
            and isinstance(operand_type, InstanceType)
            and isinstance(operand_type.typ, RecordType)
        ):
            dunder = DUNDER_MAP[operation.__class__]
            operand_class_name = operand_type.typ.record.name
            method_name = f"{operand_class_name}_+_{dunder}"
            if any([method_name in scope for scope in self.scopes]):
                call = ast.Call(
                    func=ast.Attribute(
                        value=operand,
                        attr=dunder,
                        ctx=ast.Load(),
                    ),
                    args=args,
                    keywords=[],
                )
                call.func.orig_id = f"{operand_class_name}.{dunder}"
                call.func.id = method_name
                call = self.visit_Call(call)
                if (dunder == "__contains__" and isinstance(operation, ast.NotIn)) or (
                    dunder == "__bool__" and isinstance(operation, ast.Not)
                ):
                    # we need to negate the result
                    not_call = TypedUnaryOp(
                        op=ast.Not(), operand=call, typ=BoolInstanceType
                    )
                    return not_call
                return call
        # if this is not supported, try the reverse dunder
        # note we assume 1, i.e. allow only a single right operand
        right_op_typ = args[0].typ if len(args) == 1 else None
        if (
            operation.__class__ in DUNDER_REVERSE_MAP
            and isinstance(right_op_typ, InstanceType)
            and isinstance(right_op_typ.typ, RecordType)
        ):
            dunder = DUNDER_REVERSE_MAP[operation.__class__]
            right_class_name = right_op_typ.typ.record.name
            method_name = f"{right_class_name}_+_{dunder}"
            if any([method_name in scope for scope in self.scopes]):
                call = ast.Call(
                    func=ast.Attribute(
                        value=args[0],
                        attr=dunder,
                        ctx=ast.Load(),
                    ),
                    args=[operand],
                    keywords=[],
                )
                call.func.orig_id = f"{right_class_name}.{dunder}"
                call.func.id = method_name
                return self.visit_Call(call)
        return None

    def type_from_annotation(self, ann: expr):
        if isinstance(ann, Constant):
            if ann.value is None:
                return UnitType()
            else:
                for scope in reversed(self.scopes):
                    for key, value in scope.items():
                        if (
                            isinstance(value, RecordType)
                            and value.record.orig_name == ann.value
                        ):
                            return value

        if isinstance(ann, Name):
            if ann.id in ATOMIC_TYPES:
                return ATOMIC_TYPES[ann.id]
            if ann.id == "Self":
                v_t = self.variable_type(ann.idSelf_new)
            elif ann.id in ["Union", "List", "Dict"]:
                raise TypeInferenceError(
                    f"Annotation {ann.id} is not allowed as a variable type, use List[Anything], Dict[Anything, Anything] or Union[...] instead"
                )
            else:
                v_t = self.variable_type(ann.id)
            if isinstance(v_t, ClassType):
                return v_t
            raise TypeInferenceError(
                f"Class name {ann.orig_id} not initialized before annotating variable"
            )
        if isinstance(ann, Subscript):
            assert isinstance(
                ann.value, Name
            ), "Only Union, Dict and List are allowed as Generic types"
            if ann.value.orig_id == "Union":
                if isinstance(ann.slice, Name):
                    elts = [ann.slice]
                elif isinstance(ann.slice, ast.Tuple):
                    elts = ann.slice.elts
                else:
                    raise TypeInferenceError(
                        "Union must combine several classes, use Union[Class1, Class2, ...]"
                    )
                # only allow List[Anything] and Dict[Anything, Anything] in unions
                for elt in elts:
                    if isinstance(elt, Subscript) and elt.value.id == "List":
                        assert (
                            isinstance(elt.slice, Name)
                            and elt.slice.orig_id == "Anything"
                        ), f"Only List[Anything] is supported in Unions. Received List[{elt.slice.orig_id}]."
                    if isinstance(elt, Subscript) and elt.value.id == "Dict":
                        assert all(
                            isinstance(e, Name) and e.orig_id == "Anything"
                            for e in elt.slice.elts
                        ), f"Only Dict[Anything, Anything] is supported in Unions. Received Dict[{elt.slice.elts[0].orig_id}, {elt.slice.elts[1].orig_id}]."
                ann_types = frozenlist([self.type_from_annotation(e) for e in elts])
                # flatten encountered union types
                ann_types = frozenlist(
                    sum(
                        (
                            tuple(t.typs) if isinstance(t, UnionType) else (t,)
                            for t in ann_types
                        ),
                        start=(),
                    )
                )
                # check for unique constr_ids
                constr_ids = [
                    record.record.constructor
                    for record in ann_types
                    if isinstance(record, RecordType)
                ]
                assert len(constr_ids) == len(set(constr_ids)), (
                    "Union must combine PlutusData classes with unique CONSTR_ID, but found duplicates: "
                    + str(
                        {
                            e.record.orig_name: e.record.constructor
                            for e in ann_types
                            if isinstance(e, RecordType)
                        }
                    )
                )
                return union_types(*ann_types)
            if ann.value.orig_id == "List":
                ann_type = self.type_from_annotation(ann.slice)
                assert isinstance(
                    ann_type, ClassType
                ), "List must have a single type as parameter"
                assert not isinstance(
                    ann_type, TupleType
                ), "List can currently not hold tuples"
                return ListType(InstanceType(ann_type))
            if ann.value.orig_id == "Dict":
                assert isinstance(ann.slice, Tuple), "Dict must combine two classes"
                assert len(ann.slice.elts) == 2, "Dict must combine two classes"
                ann_types = self.type_from_annotation(
                    ann.slice.elts[0]
                ), self.type_from_annotation(ann.slice.elts[1])
                assert all(
                    isinstance(e, ClassType) for e in ann_types
                ), "Dict must combine two classes"
                assert not any(
                    isinstance(e, TupleType) for e in ann_types
                ), "Dict can currently not hold tuples"
                return DictType(*(InstanceType(a) for a in ann_types))
            if ann.value.orig_id == "Tuple":
                assert isinstance(
                    ann.slice, Tuple
                ), "Tuple must combine several classes"
                ann_types = [self.type_from_annotation(e) for e in ann.slice.elts]
                assert all(
                    isinstance(e, ClassType) for e in ann_types
                ), "Tuple must combine classes"
                return TupleType(frozenlist([InstanceType(a) for a in ann_types]))
            raise NotImplementedError(
                "Only Union, Dict and List are allowed as Generic types"
            )
        if ann is None:
            return AnyType()
        raise NotImplementedError(f"Annotation type {ann.__class__} is not supported")

    def resolve_self_annotations(self, node: FunctionDef) -> FunctionDef:
        """Replace Self annotations with the concrete class name captured during scoping."""
        node_cp = copy(node)
        node_cp.args = copy(node.args)
        node_cp.args.args = [copy(a) for a in node.args.args]
        node_cp.returns = copy(node.returns)
        if not node_cp.args.args:
            return node_cp
        self_ann = node_cp.args.args[0].annotation
        for arg in node_cp.args.args:
            if hasattr(arg.annotation, "idSelf"):
                arg.annotation = copy(arg.annotation)
                arg.annotation.id = self_ann.id
        if hasattr(node_cp.returns, "idSelf"):
            node_cp.returns.id = self_ann.id
        return node_cp

    def function_bound_names(self, node: FunctionDef) -> typing.Set[str]:
        for scope in reversed(self.function_bound_name_scopes):
            if id(node) in scope:
                return scope[id(node)]
        source_node_id = getattr(node, "bound_name_source_id", None)
        if source_node_id is not None:
            transformed_bound_names = {
                v for v in externally_bound_vars(node) if v not in ["List", "Dict"]
            }
            for scope in reversed(self.function_bound_name_scopes):
                if source_node_id in scope:
                    return set(scope[source_node_id]).union(transformed_bound_names)
        return {v for v in externally_bound_vars(node) if v not in ["List", "Dict"]}

    def function_needs_self_binding(self, node: FunctionDef) -> bool:
        return node.name in self.function_bound_names(node)

    def function_bound_var_types(
        self, node: FunctionDef, allow_uninitialized: bool
    ) -> typing.Dict[str, Type]:
        needs_self_binding = self.function_needs_self_binding(node)
        bound_vars = {}
        for name in sorted(self.function_bound_names(node)):
            if name in ["List", "Dict"]:
                continue
            if needs_self_binding and name == node.name:
                continue
            try:
                bound_vars[name] = self.variable_type(name)
            except TypeInferenceError:
                if not allow_uninitialized:
                    raise
                # Provisionally type forward references; the final pass overwrites this.
                bound_vars[name] = InstanceType(AnyType())
        return bound_vars

    def build_function_type(
        self,
        node: FunctionDef,
        arg_types: typing.Iterable[Type],
        allow_uninitialized_bound_vars: bool,
        bound_var_source_node: typing.Optional[FunctionDef] = None,
    ) -> FunctionType:
        source_node = (
            bound_var_source_node if bound_var_source_node is not None else node
        )
        return FunctionType(
            frozenlist(arg_types),
            InstanceType(self.type_from_annotation(node.returns)),
            bound_vars=self.function_bound_var_types(
                source_node, allow_uninitialized=allow_uninitialized_bound_vars
            ),
            bind_self=(
                node.name if self.function_needs_self_binding(source_node) else None
            ),
        )

    def declare_class_type(self, node: ClassDef, force: bool) -> RecordType:
        class_record = RecordReader(self).extract(node)
        typ = RecordType(class_record)
        self.set_variable_type(node.name, typ, force=force)
        self.FUNCTION_ARGUMENT_REGISTRY[node.name] = [
            typedarg(arg=field, typ=field_typ, orig_arg=field)
            for field, field_typ in class_record.fields
        ]
        return typ

    def predeclare_class_symbols(self, node_seq: typing.List[stmt]):
        class_nodes = []
        seen_names = set()
        for stmt in node_seq:
            if isinstance(stmt, ClassDef) and stmt.name not in seen_names:
                class_nodes.append(stmt)
                seen_names.add(stmt.name)
        pending = class_nodes
        unresolved = {}
        while pending:
            next_pending = []
            progress = False
            for class_node in pending:
                try:
                    self.declare_class_type(class_node, force=True)
                    progress = True
                except TypeInferenceError as e:
                    unresolved[class_node.name] = e
                    next_pending.append(class_node)
            if not progress and next_pending:
                # Some imported class graphs can only be resolved later in strict statement order.
                break
            pending = next_pending

    def predeclare_function_symbols(self, node_seq: typing.List[stmt]):
        declared_names = set()
        for stmt in node_seq:
            if not isinstance(stmt, FunctionDef):
                continue
            if stmt.name in declared_names:
                # Keep first-definition semantics for compatibility checks.
                continue
            try:
                resolved = self.resolve_self_annotations(stmt)
                arg_types = [
                    InstanceType(self.type_from_annotation(arg.annotation))
                    for arg in resolved.args.args
                ]
                functyp = self.build_function_type(
                    resolved,
                    arg_types=arg_types,
                    allow_uninitialized_bound_vars=True,
                    bound_var_source_node=stmt,
                )
                self.set_variable_type(stmt.name, InstanceType(functyp), force=True)
                self.FUNCTION_ARGUMENT_REGISTRY[stmt.name] = stmt.args.args
                declared_names.add(stmt.name)
            except TypeInferenceError:
                # Some imported helpers can only be typed after earlier declarations.
                # Defer those to the main definition pass.
                continue

    def predeclare_sequence_symbols(self, node_seq: typing.List[stmt]):
        self.predeclare_class_symbols(node_seq)
        self.predeclare_function_symbols(node_seq)

    def compute_transitive_function_bound_names(
        self, node_seq: typing.List[stmt]
    ) -> typing.Dict[int, typing.Set[str]]:
        function_nodes = [n for n in node_seq if isinstance(n, FunctionDef)]
        if not function_nodes:
            return {}

        first_binding_index = {}
        for i, stmt_node in enumerate(node_seq):
            if isinstance(stmt_node, FunctionDef):
                first_binding_index.setdefault(stmt_node.name, i)
            elif isinstance(stmt_node, ClassDef):
                first_binding_index.setdefault(stmt_node.name, i)
            elif isinstance(stmt_node, Assign):
                for target in stmt_node.targets:
                    if isinstance(target, Name):
                        first_binding_index.setdefault(target.id, i)
            elif isinstance(stmt_node, AnnAssign):
                if isinstance(stmt_node.target, Name):
                    first_binding_index.setdefault(stmt_node.target.id, i)
            elif isinstance(stmt_node, Import):
                for imported in stmt_node.names:
                    bound_name = imported.asname or imported.name.split(".")[0]
                    first_binding_index.setdefault(bound_name, i)
            elif isinstance(stmt_node, ImportFrom):
                for imported in stmt_node.names:
                    bound_name = imported.asname or imported.name
                    first_binding_index.setdefault(bound_name, i)

        function_stmt_index = {
            id(stmt_node): i
            for i, stmt_node in enumerate(node_seq)
            if isinstance(stmt_node, FunctionDef)
        }

        first_def_index = {}
        first_def_node_by_name = {}
        for i, node in enumerate(function_nodes):
            if node.name in first_def_index:
                continue
            first_def_index[node.name] = i
            first_def_node_by_name[node.name] = node
        function_names = set(first_def_index.keys())

        direct_nonfunc = {}
        direct_called_funcs = {}
        required_direct_funcs = {}
        for node in function_nodes:
            node_id = id(node)
            direct = {
                v for v in externally_bound_vars(node) if v not in ["List", "Dict"]
            }
            called_funcs = {v for v in direct if v in function_names}
            direct_called_funcs[node_id] = called_funcs
            direct_nonfunc[node_id] = direct.difference(called_funcs)

            required = set()
            if node.name in read_vars(node):
                # Self-recursion needs explicit self binding in function parameters.
                required.add(node.name)
            for fn_name in called_funcs:
                # Backward references are available via lexical scoping.
                # Forward references need runtime binding through closure parameters.
                if first_def_index[fn_name] > first_def_index[node.name]:
                    required.add(fn_name)
            for sibling_name in getattr(node, "self_called_method_names", set()):
                if sibling_name in function_names and (
                    first_def_index[sibling_name] > first_def_index[node.name]
                ):
                    required.add(sibling_name)
            required_direct_funcs[node_id] = required

        node_by_id = {id(node): node for node in function_nodes}
        graph = {
            id(node): [
                id(first_def_node_by_name[fn_name])
                for fn_name in direct_called_funcs[id(node)]
                if fn_name in first_def_node_by_name
            ]
            for node in function_nodes
        }

        index = 0
        stack = []
        stack_members = set()
        indices = {}
        lowlinks = {}
        recursive_component_names = {}

        def strongconnect(node_id: int):
            nonlocal index
            indices[node_id] = index
            lowlinks[node_id] = index
            index += 1
            stack.append(node_id)
            stack_members.add(node_id)

            for dep_id in graph[node_id]:
                if dep_id not in indices:
                    strongconnect(dep_id)
                    lowlinks[node_id] = min(lowlinks[node_id], lowlinks[dep_id])
                elif dep_id in stack_members:
                    lowlinks[node_id] = min(lowlinks[node_id], indices[dep_id])

            if lowlinks[node_id] != indices[node_id]:
                return

            component = []
            while True:
                member = stack.pop()
                stack_members.remove(member)
                component.append(member)
                if member == node_id:
                    break

            if len(component) > 1 or node_id in graph[node_id]:
                component_names = {node_by_id[member].name for member in component}
            else:
                component_names = set()
            for member in component:
                recursive_component_names[member] = component_names

        for node in function_nodes:
            node_id = id(node)
            if node_id not in indices:
                strongconnect(node_id)

        for node in function_nodes:
            node_id = id(node)
            recursive_component_names.setdefault(node_id, set())

        symbol_bound: typing.Dict[int, typing.Set[str]] = {
            id(node): set(direct_nonfunc[id(node)])
            .union(required_direct_funcs[id(node)])
            .union(recursive_component_names[id(node)])
            for node in function_nodes
        }
        changed = True
        while changed:
            changed = False
            new_symbol_bound = {}
            for node in function_nodes:
                node_id = id(node)
                resolved = set(direct_nonfunc[node_id]).union(
                    required_direct_funcs[node_id]
                )
                for dep_name in direct_called_funcs[node_id]:
                    dep_node = first_def_node_by_name.get(dep_name)
                    if dep_node is None:
                        continue
                    for dep_req_name in symbol_bound[id(dep_node)]:
                        if dep_req_name not in function_names:
                            continue
                        # Transitive function dependencies must still be threaded
                        # through the caller even if the original symbol is
                        # defined earlier in the module. Once the callee closes
                        # over that function, callers need to supply the same
                        # runtime binding to keep recursive call signatures
                        # aligned.
                        resolved.add(dep_req_name)
                new_symbol_bound[node_id] = resolved
            changed = any(
                new_symbol_bound[id(node)] != symbol_bound[id(node)]
                for node in function_nodes
            )
            symbol_bound = new_symbol_bound
        return {id(node): symbol_bound[id(node)] for node in function_nodes}

    def lower_class_methods_in_sequence(
        self, node_seq: typing.List[stmt]
    ) -> typing.List[stmt]:
        node_seq_cp = list(node_seq)
        additional_functions = []
        for n in node_seq_cp:
            if not isinstance(n, ast.ClassDef):
                continue
            method_names = {
                attribute.name
                for attribute in n.body
                if isinstance(attribute, ast.FunctionDef)
            }
            non_method_attributes = []
            for attribute in n.body:
                if not isinstance(attribute, ast.FunctionDef):
                    non_method_attributes.append(attribute)
                    continue
                func = copy(attribute)
                if func.name[0:2] == "__" and func.name[-2:] == "__":
                    assert (
                        func.name in ALL_DUNDERS
                    ), f"The following Dunder methods are supported {sorted(ALL_DUNDERS)}. Received {func.name} which is not supported"
                func.name = f"{n.name}_+_{attribute.name}"

                def does_literally_reference_self(arg):
                    if arg is None:
                        return False
                    if isinstance(arg, Name) and arg.id == n.name:
                        return True
                    if (
                        isinstance(arg, ast.Subscript)
                        and isinstance(arg.value, Name)
                        and arg.value.id in ("Union", "List", "Dict")
                    ):
                        # Only possible for List, Dict and Union
                        if any(
                            does_literally_reference_self(e) for e in arg.slice.elts
                        ):
                            return True
                    return False

                for arg in func.args.args:
                    assert not does_literally_reference_self(
                        arg.annotation
                    ), f"Argument '{arg.arg}' of method '{attribute.name}' in class '{n.name}' literally references the class itself. This is not allowed. If you want to reference the class itself, use 'Self' as type annotation."
                assert not does_literally_reference_self(
                    func.returns
                ), f"Return type of method '{attribute.name}' in class '{n.name}' literally references the class itself. This is not allowed. If you want to reference the class itself, use 'Self' as type annotation."
                ann = ast.Name(id=n.name, ctx=ast.Load())
                if len(func.args.args) == 0:
                    raise TypeError(
                        f"Method '{attribute.orig_name}' in class '{n.orig_name}' must have at least one argument (self)"
                    )
                custom_fix_missing_locations(ann, attribute.args.args[0])
                if func.args.args[0].orig_arg != "self":
                    OPSHIN_LOGGER.warning(
                        f"The first argument of method '{attribute.name}' in class '{n.orig_name}' should be named 'self', but found '{func.args.args[0].orig_arg}'. This is not enforced, but recommended."
                    )
                if func.args.args[0].annotation is not None and not (
                    isinstance(func.args.args[0].annotation, Name)
                    and func.args.args[0].annotation.id == "Self"
                ):
                    raise TypeError(
                        f"The first argument of method '{attribute.name}' in class '{n.name}' must either not be annotated or be annotated with 'Self' to indicate that it is the instance of the class."
                    )
                ann.orig_id = attribute.args.args[0].orig_arg
                func.args.args[0].annotation = ann

                self_arg_name = attribute.args.args[0].arg

                class SelfMethodCallCollector(NodeVisitor):
                    def __init__(self):
                        self.called = set()

                    def visit_Call(self, node: Call):
                        if (
                            isinstance(node.func, Attribute)
                            and isinstance(node.func.value, Name)
                            and node.func.value.id == self_arg_name
                            and node.func.attr in method_names
                        ):
                            self.called.add(node.func.attr)
                        self.generic_visit(node)

                called_self_methods = SelfMethodCallCollector()
                called_self_methods.visit(attribute)
                func.self_called_method_names = {
                    f"{n.name}_+_{method_name}"
                    for method_name in called_self_methods.called
                }
                additional_functions.append(func)
            n.body = non_method_attributes
        if additional_functions:
            last = node_seq_cp.pop()
            node_seq_cp.extend(additional_functions)
            node_seq_cp.append(last)
        return node_seq_cp

    def visit_sequence(self, node_seq: typing.List[stmt]) -> plt.AST:
        node_seq = self.lower_class_methods_in_sequence(node_seq)
        function_bound_names = self.compute_transitive_function_bound_names(node_seq)
        first_function_defs = set()
        seen_function_names = set()
        for node in node_seq:
            if isinstance(node, FunctionDef) and node.name not in seen_function_names:
                first_function_defs.add(id(node))
                seen_function_names.add(node.name)
        self.function_bound_name_scopes.append(function_bound_names)
        self.first_function_definition_scopes.append(first_function_defs)
        try:
            self.predeclare_sequence_symbols(node_seq)

            typed_stmts = [None] * len(node_seq)
            prevtyps = {}

            for i, node in enumerate(node_seq):
                if isinstance(node, FunctionDef):
                    continue
                stmt = self.visit(node)
                typed_stmts[i] = stmt
                # if an assert is among the statements apply the isinstance cast
                if isinstance(stmt, Assert):
                    typchecks, _ = TypeCheckVisitor(
                        self.allow_isinstance_anything
                    ).visit(stmt.test)
                    # for the time after this assert, the variable has the specialized type
                    wrapped = self.implement_typechecks(typchecks)
                    prevtyps.update(wrapped)
                    self.wrapped.extend(wrapped.keys())
            self.implement_typechecks(prevtyps)

            for i, node in enumerate(node_seq):
                if isinstance(node, FunctionDef):
                    typed_stmts[i] = self.visit(node)

            seen_function_def = False
            for i, node in enumerate(node_seq):
                if isinstance(node, FunctionDef):
                    seen_function_def = True
                    continue
                if seen_function_def:
                    typed_stmts[i] = self.visit(node)

            return typed_stmts
        finally:
            self.first_function_definition_scopes.pop()
            self.function_bound_name_scopes.pop()

    def visit_ClassDef(self, node: ClassDef) -> TypedClassDef:
        typ = self.declare_class_type(node, force=True)
        typed_node = copy(node)
        typed_node.class_typ = typ
        return typed_node

    def visit_Constant(self, node: Constant) -> TypedConstant:
        tc = copy(node)
        assert type(node.value) not in [
            float,
            complex,
            type(...),
        ], "Float, complex numbers and ellipsis currently not supported"
        tc.typ = constant_type(node.value)
        return tc

    def visit_NoneType(self, node: None) -> TypedConstant:
        tc = Constant(value=None)
        tc.typ = constant_type(tc.value)
        return tc

    def visit_Tuple(self, node: Tuple) -> TypedTuple:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = InstanceType(TupleType(frozenlist([e.typ for e in tt.elts])))
        return tt

    def visit_List(self, node: List) -> TypedList:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        assert all(
            isinstance(e.typ, InstanceType) for e in tt.elts
        ), f"All list elements must be instances of a class, found class types {', '.join(e.typ.python_type() for e in tt.elts if not isinstance(e.typ, InstanceType))}"
        # try to derive a max type
        max_typ = find_max_type(tt.elts)
        tt.typ = InstanceType(ListType(max_typ))
        return tt

    def visit_Dict(self, node: Dict) -> TypedDict:
        tt = copy(node)
        tt.keys = [self.visit(k) for k in node.keys]
        tt.values = [self.visit(v) for v in node.values]
        assert all(
            isinstance(e.typ, InstanceType) for e in tt.keys
        ), f"All keys of a dict must be instances of a class, found class types {', '.join(e.typ.python_type() for e in tt.keys if not isinstance(e.typ, InstanceType))}"
        # try to derive a max type
        k_typ = find_max_type(tt.keys)
        v_typ = find_max_type(tt.values)
        tt.typ = InstanceType(DictType(k_typ, v_typ))
        return tt

    def visit_Assign(self, node: Assign) -> TypedAssign:
        typed_ass = copy(node)
        typed_ass.value: TypedExpression = self.visit(node.value)
        # Make sure to first set the type of each target name so we can load it when visiting it
        for t in node.targets:
            assert isinstance(
                t, Name
            ), "Can only assign to variable names (e.g., x = 5 or a, b = 10, 20). OpShin does not allow assigning to dicts, lists, or members (e.g., x[0] = 1; x.foo = 1)"
            # Check compatibility to previous types -> variable can be bound in a function before and needs to maintain type
            self.set_variable_type(t.id, typed_ass.value.typ)
        typed_ass.targets = [self.visit(t) for t in node.targets]
        # for deconstructed tuples, check that the size matches
        if hasattr(typed_ass.value, "is_tuple_with_deconstruction"):
            assert isinstance(typed_ass.value.typ, InstanceType) and (
                isinstance(typed_ass.value.typ.typ, TupleType)
                or isinstance(typed_ass.value.typ.typ, PairType)
            ), f"Tuple deconstruction expected a tuple type, found '{typed_ass.value.typ.python_type()}'"
            if isinstance(typed_ass.value.typ.typ, PairType):
                assert (
                    typed_ass.value.is_tuple_with_deconstruction == 2
                ), f"Too many values to unpack or not enough values to unpack. Tuple deconstruction required assigning to 2 elements found '{typed_ass.value.is_tuple_with_deconstruction}'"
            else:
                assert typed_ass.value.is_tuple_with_deconstruction == len(
                    typed_ass.value.typ.typ.typs
                ), f"Too many values to unpack or not enough values to unpack. Tuple deconstruction required tuple with {typed_ass.value.is_tuple_with_deconstruction} elements found '{typed_ass.value.typ.python_type()}'"
        return typed_ass

    def visit_AnnAssign(self, node: AnnAssign) -> TypedAnnAssign:
        typed_ass = copy(node)
        typed_ass.annotation = self.type_from_annotation(node.annotation)
        if isinstance(typed_ass.annotation, ListType) and (
            (isinstance(node.value, Constant) and node.value.value == [])
            or (isinstance(node.value, List) and node.value.elts == [])
        ):
            # Empty lists are only allowed in annotated assignments
            typed_ass.value: TypedExpression = copy(node.value)
            typed_ass.value.typ = InstanceType(typed_ass.annotation)
        elif isinstance(typed_ass.annotation, DictType) and (
            (isinstance(node.value, Constant) and node.value.value == {})
            or (
                isinstance(node.value, Dict)
                and node.value.keys == []
                and node.value.values == []
            )
        ):
            # Empty lists are only allowed in annotated assignments
            typed_ass.value: TypedExpression = copy(node.value)
            typed_ass.value.typ = InstanceType(typed_ass.annotation)
        else:
            typed_ass.value: TypedExpression = self.visit(node.value)
        assert isinstance(
            node.target, Name
        ), "Can only assign to variable names, no type deconstruction"
        # Check compatibility to previous types -> variable can be bound in a function before and needs to maintain type
        self.set_variable_type(node.target.id, InstanceType(typed_ass.annotation))
        typed_ass.target = self.visit(node.target)
        assert (
            typed_ass.value.typ >= InstanceType(typed_ass.annotation)
            or InstanceType(typed_ass.annotation) >= typed_ass.value.typ
        ), "Can only cast between related types"
        return typed_ass

    def visit_If(self, node: If) -> TypedIf:
        typed_if = copy(node)
        typed_if.test = self.visit(node.test)
        assert (
            typed_if.test.typ == BoolInstanceType
        ), "Branching condition must have boolean type"
        typchecks, inv_typchecks = TypeCheckVisitor(
            self.allow_isinstance_anything
        ).visit(typed_if.test)
        # for the time of the branch, these types are cast
        initial_scope = copy(self.scopes[-1])
        wrapped = self.implement_typechecks(typchecks)
        self.wrapped.extend(wrapped.keys())
        typed_if.body = self.visit_sequence(node.body)
        self.wrapped = [x for x in self.wrapped if x not in wrapped.keys()]

        # save resulting types
        final_scope_body = copy(self.scopes[-1])
        # reverse typechecks and remove typing of one branch
        self.scopes[-1] = initial_scope
        # for the time of the else branch, the inverse types hold
        wrapped = self.implement_typechecks(inv_typchecks)
        self.wrapped.extend(wrapped.keys())
        typed_if.orelse = self.visit_sequence(node.orelse)
        self.wrapped = [x for x in self.wrapped if x not in wrapped.keys()]
        final_scope_else = self.scopes[-1]
        # unify the resulting branch scopes
        self.scopes[-1] = merge_scope(final_scope_body, final_scope_else)
        return typed_if

    def visit_While(self, node: While) -> TypedWhile:
        typed_while = copy(node)
        typed_while.test = self.visit(node.test)
        assert (
            typed_while.test.typ == BoolInstanceType
        ), "Branching condition must have boolean type"
        typchecks, inv_typchecks = TypeCheckVisitor(
            self.allow_isinstance_anything
        ).visit(typed_while.test)
        # for the time of the branch, these types are cast
        initial_scope = copy(self.scopes[-1])
        wrapped = self.implement_typechecks(typchecks)
        self.wrapped.extend(wrapped.keys())
        typed_while.body = self.visit_sequence(node.body)
        self.wrapped = [x for x in self.wrapped if x not in wrapped.keys()]
        final_scope_body = copy(self.scopes[-1])
        # revert changes
        self.scopes[-1] = initial_scope
        # for the time of the else branch, the inverse types hold
        wrapped = self.implement_typechecks(inv_typchecks)
        self.wrapped.extend(wrapped.keys())
        typed_while.orelse = self.visit_sequence(node.orelse)
        self.wrapped = [x for x in self.wrapped if x not in wrapped.keys()]
        final_scope_else = self.scopes[-1]
        self.scopes[-1] = merge_scope(final_scope_body, final_scope_else)
        return typed_while

    def visit_For(self, node: For) -> TypedFor:
        typed_for = copy(node)
        typed_for.iter = self.visit(node.iter)
        if isinstance(node.target, Tuple):
            raise NotImplementedError(
                "Tuple deconstruction in for loops is not supported yet"
            )
        vartyp = None
        itertyp = typed_for.iter.typ
        assert isinstance(
            itertyp, InstanceType
        ), "Can only iterate over instances, not classes"
        if isinstance(itertyp.typ, TupleType):
            assert itertyp.typ.typs, "Iterating over an empty tuple is not allowed"
            vartyp = itertyp.typ.typs[0]
            assert all(
                itertyp.typ.typs[0] == t for t in itertyp.typ.typs
            ), f"Iterating through a tuple requires the same type for each element, found tuple of type {itertyp.typ.python_type()}"
        elif isinstance(itertyp.typ, ListType):
            vartyp = itertyp.typ.typ
        else:
            raise NotImplementedError(
                "Type inference for loops over non-list and non-tuple objects is not supported"
            )
        self.set_variable_type(node.target.id, vartyp)
        typed_for.target = self.visit(node.target)
        typed_for.body = self.visit_sequence(node.body)
        typed_for.orelse = self.visit_sequence(node.orelse)
        return typed_for

    def visit_Name(self, node: Name) -> TypedName:
        tn = copy(node)
        # typing List and Dict are not present in scope we don't want to call variable_type
        if node.orig_id == "List":
            tn.typ = ListType(InstanceType(AnyType()))
        elif node.orig_id == "Dict":
            tn.typ = DictType(InstanceType(AnyType()), InstanceType(AnyType()))
        else:
            # Make sure that the rhs of an assign is evaluated first
            tn.typ = self.variable_type(node.id)
        if node.id in self.wrapped:
            tn.is_wrapped = True
        return tn

    def visit_keyword(self, node: keyword) -> Typedkeyword:
        tk = copy(node)
        tk.value = self.visit(node.value)
        return tk

    def visit_Compare(self, node: Compare) -> Union[TypedCompare, TypedCall]:
        dunder_node = self.dunder_override(node)
        if dunder_node is not None:
            return dunder_node
        typed_cmp = copy(node)
        typed_cmp.left = self.visit(node.left)
        typed_cmp.comparators = [self.visit(s) for s in node.comparators]
        typed_cmp.typ = BoolInstanceType

        return typed_cmp

    def visit_arg(self, node: arg) -> typedarg:
        ta = copy(node)
        ta.typ = InstanceType(self.type_from_annotation(node.annotation))
        self.set_variable_type(ta.arg, ta.typ)
        return ta

    def visit_arguments(self, node: arguments) -> typedarguments:
        if node.kw_defaults or node.kwarg or node.kwonlyargs or node.defaults:
            raise NotImplementedError(
                "Keyword arguments and defaults not supported yet"
            )
        ta = copy(node)
        ta.args = [self.visit(a) for a in node.args]
        return ta

    def visit_FunctionDef(self, node: FunctionDef) -> TypedFunctionDef:
        resolved_node = self.resolve_self_annotations(node)
        tfd = copy(resolved_node)
        tfd.bound_name_source_id = id(node)
        wraps_builtin = (
            all(
                isinstance(o, Name) and o.orig_id == "wraps_builtin"
                for o in resolved_node.decorator_list
            )
            and resolved_node.decorator_list
        )
        assert (
            not resolved_node.decorator_list or wraps_builtin
        ), f"Functions may not have decorators other than literal @wraps_builtin, found other decorators at {resolved_node.orig_name}."

        self.enter_scope()
        tfd.args = self.visit(resolved_node.args)
        arg_types = [t.typ for t in tfd.args.args]
        base_scope = copy(self.scopes[-1])

        functyp = self.build_function_type(
            resolved_node,
            arg_types=arg_types,
            allow_uninitialized_bound_vars=wraps_builtin,
            bound_var_source_node=node,
        )
        tfd.typ = InstanceType(functyp)
        if wraps_builtin:
            # the body of wrapping builtin functions is fully ignored
            pass
        else:
            # We need the function type inside for (co-)recursion.
            self.scopes[-1] = copy(base_scope)
            self.set_variable_type(resolved_node.name, tfd.typ, force=True)
            tfd.body = self.visit_sequence(resolved_node.body)
            # Recompute closure bindings from the transformed body.
            # Dunder rewrites can introduce additional free names that are not visible
            # in the original AST shape used during pre-declaration.
            updated_typ = InstanceType(
                self.build_function_type(
                    resolved_node,
                    arg_types=arg_types,
                    allow_uninitialized_bound_vars=wraps_builtin,
                    bound_var_source_node=tfd,
                )
            )
            if updated_typ != tfd.typ:
                # Revisit the body with the final function shape so recursive call sites
                # receive the same closure parameters as external call sites.
                tfd.typ = updated_typ
                self.scopes[-1] = copy(base_scope)
                self.set_variable_type(resolved_node.name, tfd.typ, force=True)
                tfd.body = self.visit_sequence(resolved_node.body)
                updated_typ = InstanceType(
                    self.build_function_type(
                        resolved_node,
                        arg_types=arg_types,
                        allow_uninitialized_bound_vars=wraps_builtin,
                        bound_var_source_node=tfd,
                    )
                )
            tfd.typ = updated_typ
            # Check that return type and annotated return type match
            rets_extractor = ReturnExtractor(functyp.rettyp)
            rets_extractor.check_fulfills(tfd)

        self.exit_scope()
        is_first_definition = (
            not self.first_function_definition_scopes
            or id(node) in self.first_function_definition_scopes[-1]
        )
        # We need the function type outside for usage.
        self.set_variable_type(resolved_node.name, tfd.typ, force=is_first_definition)
        self.FUNCTION_ARGUMENT_REGISTRY[resolved_node.name] = resolved_node.args.args
        return tfd

    def visit_Module(self, node: Module) -> TypedModule:
        self.enter_scope()
        tm = copy(node)
        tm.body = self.visit_sequence(node.body)
        self.exit_scope()
        return tm

    def visit_Expr(self, node: Expr) -> TypedExpr:
        tn = copy(node)
        tn.value = self.visit(node.value)
        return tn

    def visit_BinOp(self, node: BinOp) -> Union[TypedBinOp, TypedCall]:
        dunder_node = self.dunder_override(node)
        if dunder_node is not None:
            return dunder_node
        tb = copy(node)
        tb.left = self.visit(node.left)
        tb.right = self.visit(node.right)
        try:
            binop_fun_typ: FunctionType = tb.left.typ.binop_type(tb.op, tb.right.typ)
        except NotImplementedError as e:
            try:
                # attempt reverse binop
                binop_fun_typ = tb.right.typ.rbinop_type(tb.op, tb.left.typ)
            except NotImplementedError:
                raise e
        tb.typ = binop_fun_typ.rettyp

        return tb

    def visit_BoolOp(self, node: BoolOp) -> TypedBoolOp:
        tt = copy(node)
        if isinstance(node.op, And):
            values = []
            prevtyps = {}
            for e in node.values:
                e_visited = self.visit(e)
                values.append(e_visited)
                typchecks, _ = TypeCheckVisitor(self.allow_isinstance_anything).visit(
                    e_visited
                )
                # for the time after the shortcut and the variable type to the specialized type
                wrapped = self.implement_typechecks(typchecks)
                self.wrapped.extend(wrapped.keys())
                prevtyps.update(wrapped)
            # Clean up wrapped variables after processing all values
            for var in prevtyps.keys():
                if var in self.wrapped:
                    self.wrapped.remove(var)
            self.implement_typechecks(prevtyps)
            tt.values = values
        elif isinstance(node.op, Or):
            values = []
            prevtyps = {}
            for e in node.values:
                values.append(self.visit(e))
                _, inv_typechecks = TypeCheckVisitor(
                    self.allow_isinstance_anything
                ).visit(values[-1])
                # for the time after the shortcut or the variable type is *not* the specialized type
                wrapped = self.implement_typechecks(inv_typechecks)
                self.wrapped.extend(wrapped.keys())
                prevtyps.update(wrapped)
            # Clean up wrapped variables after processing all values
            for var in prevtyps.keys():
                if var in self.wrapped:
                    self.wrapped.remove(var)
            self.implement_typechecks(prevtyps)
            tt.values = values
        else:
            raise NotImplementedError(f"Boolean operator {node.op} not supported")
        tt.typ = BoolInstanceType
        assert all(
            BoolInstanceType >= e.typ for e in tt.values
        ), f"All values compared must be bools, found {', '.join(e.typ.python_type() for e in tt.values)}"
        return tt

    def visit_UnaryOp(self, node: UnaryOp) -> TypedUnaryOp:
        dunder_node = self.dunder_override(node)
        if dunder_node is not None:
            return dunder_node
        tu = copy(node)
        tu.operand = self.visit(node.operand)
        tu.typ = tu.operand.typ.typ.unop_type(node.op).rettyp
        return tu

    def visit_Subscript(self, node: Subscript) -> TypedSubscript:
        ts = copy(node)
        # special case: Subscript of Union / Dict / List and atomic types
        if isinstance(ts.value, Name) and ts.value.orig_id in [
            "Union",
            "Dict",
            "List",
        ]:
            ts.value = ts.typ = self.type_from_annotation(ts)
            return ts

        ts.value = self.visit(node.value)
        assert isinstance(ts.value.typ, InstanceType), "Can only subscript instances"
        if isinstance(ts.value.typ.typ, TupleType):
            assert (
                ts.value.typ.typ.typs
            ), "Accessing elements from the empty tuple is not allowed"
            if isinstance(ts.slice, UnaryOp) and isinstance(ts.slice.op, USub):
                ts.slice = self.visit(Constant(-ts.slice.operand.value))
            if isinstance(ts.slice, Constant) and isinstance(ts.slice.value, int):
                assert ts.slice.value < len(
                    ts.value.typ.typ.typs
                ), f"Subscript index out of bounds for tuple. Accessing index {ts.slice.value} in tuple with {len(ts.value.typ.typ.typs)} elements ({ts.value.typ.python_type()})"
                ts.typ = ts.value.typ.typ.typs[ts.slice.value]
            else:
                raise TypeInferenceError(
                    f"Could not infer type of subscript of typ {ts.value.typ.python_type()}"
                )
        elif isinstance(ts.value.typ.typ, PairType):
            if isinstance(ts.slice, UnaryOp) and isinstance(ts.slice.op, USub):
                ts.slice = self.visit(Constant(-ts.slice.operand.value))
            if isinstance(ts.slice, Constant) and isinstance(ts.slice.value, int):
                assert (
                    -3 < ts.slice.value < 2
                ), f"Can only access -2, -1, 0 or 1 index in pairs, found {ts.slice.value}"
                ts.typ = (
                    ts.value.typ.typ.l_typ
                    if ts.slice.value % 2 == 0
                    else ts.value.typ.typ.r_typ
                )
            else:
                raise TypeInferenceError(
                    f"Could not infer type of subscript of typ {ts.value.typ.python_type()}"
                )
        elif isinstance(ts.value.typ.typ, ListType):
            if not isinstance(ts.slice, Slice):
                ts.typ = ts.value.typ.typ.typ
                ts.slice = self.visit(node.slice)
                assert (
                    ts.slice.typ == IntegerInstanceType
                ), f"List indices must be integers, found {ts.slice.typ.python_type()} for list {ts.value.typ.python_type()}"
            else:
                ts.typ = ts.value.typ
                if ts.slice.lower is None:
                    ts.slice.lower = Constant(0)
                ts.slice.lower = self.visit(node.slice.lower)
                assert (
                    ts.slice.lower.typ == IntegerInstanceType
                ), f"Lower slice indices for lists must be integers, found {ts.slice.lower.typ.python_type()} for list {ts.value.typ.python_type()}"
                if ts.slice.upper is None:
                    ts.slice.upper = Call(
                        func=Name(id="len", ctx=Load()), args=[ts.value], keywords=[]
                    )
                    ts.slice.upper.func.orig_id = "len"
                ts.slice.upper = self.visit(node.slice.upper)
                assert (
                    ts.slice.upper.typ == IntegerInstanceType
                ), f"Upper slice indices for lists must be integers, found {ts.slice.upper.typ.python_type()} for list {ts.value.typ.python_type()}"
        elif isinstance(ts.value.typ.typ, ByteStringType):
            if not isinstance(ts.slice, Slice):
                ts.typ = IntegerInstanceType
                ts.slice = self.visit(node.slice)
                assert (
                    ts.slice.typ == IntegerInstanceType
                ), f"Bytes indices must be integers, found {ts.slice.typ.python_type()}."
            else:
                ts.typ = ByteStringInstanceType
                if ts.slice.lower is None:
                    ts.slice.lower = Constant(0)
                ts.slice.lower = self.visit(node.slice.lower)
                assert (
                    ts.slice.lower.typ == IntegerInstanceType
                ), f"Lower slice indices for bytes must be integers, found {ts.slice.lower.typ.python_type()}"
                if ts.slice.upper is None:
                    ts.slice.upper = Call(
                        func=Name(id="len", ctx=Load()), args=[ts.value], keywords=[]
                    )
                    ts.slice.upper.func.orig_id = "len"
                ts.slice.upper = self.visit(node.slice.upper)
                assert (
                    ts.slice.upper.typ == IntegerInstanceType
                ), f"Upper slice indices for bytes must be integers, found {ts.slice.upper.typ.python_type()}"
        elif isinstance(ts.value.typ.typ, DictType):
            if not isinstance(ts.slice, Slice):
                ts.slice = self.visit(node.slice)
                assert (
                    ts.value.typ.typ.key_typ >= ts.slice.typ
                ), f"Dict subscript must have dict key type {ts.value.typ.typ.key_typ.python_type()} but has type {ts.slice.typ.python_type()}"
                ts.typ = ts.value.typ.typ.value_typ
            else:
                raise TypeInferenceError(
                    f"Could not infer type of subscript of dict with a slice."
                )
        else:
            raise TypeInferenceError(
                f"Could not infer type of subscript of typ {ts.value.typ.python_type()}"
            )
        return ts

    def visit_Call(self, node: Call) -> TypedCall:
        tc = copy(node)
        if node.keywords:
            assert (
                node.func.id in self.FUNCTION_ARGUMENT_REGISTRY
            ), "Keyword arguments can only be used with user defined functions"
            keywords = copy(node.keywords)
            reg_args = self.FUNCTION_ARGUMENT_REGISTRY[node.func.id]
            args = []
            for i, a in enumerate(reg_args):
                if len(node.args) > i:
                    args.append(self.visit(node.args[i]))
                else:
                    candidates = [
                        (idx, keyword)
                        for idx, keyword in enumerate(keywords)
                        if keyword.arg == a.orig_arg
                    ]
                    assert (
                        len(candidates) == 1
                    ), f"There should be one keyword or positional argument for the arg {a.orig_arg} but found {len(candidates)}"
                    args.append(self.visit(candidates[0][1].value))
                    keywords.pop(candidates[0][0])
            assert (
                len(keywords) == 0
            ), f"Could not match the keywords {[keyword.arg for keyword in keywords]} to any argument"
            tc.args = args
            tc.keywords = []
        else:
            tc.args = [self.visit(a) for a in node.args]

        # might be isinstance
        # Subscripts are not allowed in isinstance calls
        is_isinstance_call = (
            isinstance(tc.func, Name) and tc.func.orig_id == "isinstance"
        )
        if is_isinstance_call and isinstance(tc.args[1], Subscript):
            raise TypeError(
                "Subscripted generics cannot be used with class and instance checks"
            )

        # Need to handle the presence of PlutusData classes
        if is_isinstance_call and not isinstance(
            tc.args[1].typ, (ByteStringType, IntegerType, ListType, DictType)
        ):
            if (
                isinstance(tc.args[0].typ, InstanceType)
                and isinstance(tc.args[0].typ.typ, AnyType)
                and not self.allow_isinstance_anything
            ):
                raise AssertionError(
                    "OpShin does not permit checking the instance of raw Anything/Datum objects as this only checks the equality of the constructor id and nothing more. "
                    "If you are certain of what you are doing, please use the flag '--allow-isinstance-anything'."
                )
            tc.typechecks = TypeCheckVisitor(self.allow_isinstance_anything).visit(tc)

        subbed_method = False
        if isinstance(tc.func, Attribute):
            # might be a method, test whether the variable is a record and if the method exists
            accessed_var = self.visit(tc.func.value)
            if (
                isinstance(accessed_var.typ, InstanceType)
                and isinstance(accessed_var.typ.typ, RecordType)
                and tc.func.attr != "to_cbor"
            ):
                class_name = accessed_var.typ.typ.record.name
                method_name = f"{class_name}_+_{tc.func.attr}"
                # If method_name found then use this.
                if self.is_defined_in_current_scope(method_name):
                    n = ast.Name(id=method_name, ctx=ast.Load())
                    n.orig_id = node.func.attr
                    tc.func = self.visit(n)
                    tc.func.orig_id = node.func.attr
                    tc.args.insert(0, accessed_var)
                    subbed_method = True

        if not subbed_method:
            tc.func = self.visit(node.func)

        # might be a class
        if isinstance(tc.func.typ, ClassType):
            tc.func.typ = tc.func.typ.constr_type()
        # type might only turn out after the initialization (note the constr could be polymorphic)
        if isinstance(tc.func.typ, InstanceType) and isinstance(
            tc.func.typ.typ, PolymorphicFunctionType
        ):
            tc.func.typ = PolymorphicFunctionInstanceType(
                tc.func.typ.typ.polymorphic_function.type_from_args(
                    [a.typ for a in tc.args]
                ),
                tc.func.typ.typ.polymorphic_function,
            )
        if isinstance(tc.func.typ, InstanceType) and isinstance(
            tc.func.typ.typ, FunctionType
        ):
            functyp = tc.func.typ.typ
            assert len(tc.args) == len(
                functyp.argtyps
            ), f"Signature of function does not match number of arguments. Expected {len(functyp.argtyps)} arguments but got {len(tc.args)} arguments."
            # all arguments need to be subtypes of the parameter type
            for i, (a, ap) in enumerate(zip(tc.args, functyp.argtyps)):
                assert (
                    ap >= a.typ
                ), f"Signature of function does not match arguments in argument {i}. Expected this type: {ap.python_type()} but got {a.typ.python_type()}."
            tc.typ = functyp.rettyp
            return tc
        raise TypeInferenceError("Could not infer type of call")

    def visit_Pass(self, node: Pass) -> TypedPass:
        tp = copy(node)
        return tp

    def visit_Return(self, node: Return) -> TypedReturn:
        tp = copy(node)
        tp.value = self.visit(node.value)
        tp.typ = tp.value.typ
        return tp

    def visit_Attribute(self, node: Attribute) -> TypedAttribute:
        tp = copy(node)
        tp.value = self.visit(node.value)
        owner = tp.value.typ
        # accesses to field
        tp.typ = owner.attribute_type(node.attr)
        return tp

    def visit_Assert(self, node: Assert) -> TypedAssert:
        ta = copy(node)
        ta.test = self.visit(node.test)
        assert (
            ta.test.typ == BoolInstanceType
        ), "Assertions must result in a boolean type"
        if ta.msg is not None:
            ta.msg = self.visit(node.msg)
            assert (
                ta.msg.typ == StringInstanceType
            ), "Assertions must has a string message (or None)"
        return ta

    def visit_RawPlutoExpr(self, node: RawPlutoExpr) -> RawPlutoExpr:
        assert node.typ is not None, "Raw Pluto Expression is missing type annotation"
        return node

    def visit_IfExp(self, node: IfExp) -> TypedIfExp:
        node_cp = copy(node)
        node_cp.test = self.visit(node.test)
        assert node_cp.test.typ == BoolInstanceType, "Comparison must have type boolean"
        typchecks, inv_typchecks = TypeCheckVisitor(
            self.allow_isinstance_anything
        ).visit(node_cp.test)
        prevtyps = self.implement_typechecks(typchecks)
        self.wrapped.extend(prevtyps.keys())
        node_cp.body = self.visit(node.body)
        self.wrapped = [x for x in self.wrapped if x not in prevtyps.keys()]

        self.implement_typechecks(prevtyps)
        prevtyps = self.implement_typechecks(inv_typchecks)
        self.wrapped.extend(prevtyps.keys())
        node_cp.orelse = self.visit(node.orelse)
        self.wrapped = [x for x in self.wrapped if x not in prevtyps.keys()]
        self.implement_typechecks(prevtyps)
        if node_cp.body.typ >= node_cp.orelse.typ:
            node_cp.typ = node_cp.body.typ
        elif node_cp.orelse.typ >= node_cp.body.typ:
            node_cp.typ = node_cp.orelse.typ
        else:
            try:
                assert isinstance(node_cp.body.typ, InstanceType) and isinstance(
                    node_cp.orelse.typ, InstanceType
                )
                node_cp.typ = InstanceType(
                    union_types(node_cp.body.typ.typ, node_cp.orelse.typ.typ)
                )
            except AssertionError:
                raise TypeInferenceError(
                    "Branches of if-expression must return compatible types."
                )
        return node_cp

    def visit_comprehension(self, g: comprehension) -> typedcomprehension:
        new_g = copy(g)
        if isinstance(g.target, Tuple):
            raise NotImplementedError(
                "Type deconstruction in comprehensions is not supported yet"
            )
        new_g.iter = self.visit(g.iter)
        itertyp = new_g.iter.typ
        assert isinstance(
            itertyp, InstanceType
        ), "Can only iterate over instances, not classes"
        if isinstance(itertyp.typ, ListType):
            vartyp = itertyp.typ.typ
        else:
            raise NotImplementedError(
                "Iterating over non-list objects is not (yet) supported"
            )
        self.set_variable_type(g.target.id, vartyp)
        new_g.target = self.visit(g.target)
        new_g.ifs = [self.visit(i) for i in g.ifs]
        return new_g

    def visit_ListComp(self, node: ListComp) -> TypedListComp:
        typed_listcomp = copy(node)
        # inside the comprehension is a separate scope
        self.enter_scope()
        # first evaluate generators for assigned variables
        typed_listcomp.generators = [self.visit(s) for s in node.generators]

        # collect isinstance type narrowing from all conditions in all generators
        all_typechecks = {}
        for gen in typed_listcomp.generators:
            for if_expr in gen.ifs:
                typchecks, _ = TypeCheckVisitor(self.allow_isinstance_anything).visit(
                    if_expr
                )
                all_typechecks.update(typchecks)

        # apply type narrowing before evaluating the element
        wrapped = self.implement_typechecks(all_typechecks)
        self.wrapped.extend(wrapped.keys())

        # then evaluate elements with narrowed types
        typed_listcomp.elt = self.visit(node.elt)

        # clean up wrapped variables
        self.wrapped = [x for x in self.wrapped if x not in wrapped.keys()]

        self.exit_scope()
        typed_listcomp.typ = InstanceType(ListType(typed_listcomp.elt.typ))
        return typed_listcomp

    def visit_DictComp(self, node: DictComp) -> TypedDictComp:
        typed_dictcomp = copy(node)
        # inside the comprehension is a separate scope
        self.enter_scope()
        # first evaluate generators for assigned variables
        typed_dictcomp.generators = [self.visit(s) for s in node.generators]

        # collect isinstance type narrowing from all conditions in all generators
        all_typechecks = {}
        for gen in typed_dictcomp.generators:
            for if_expr in gen.ifs:
                typchecks, _ = TypeCheckVisitor(self.allow_isinstance_anything).visit(
                    if_expr
                )
                all_typechecks.update(typchecks)

        # apply type narrowing before evaluating the elements
        wrapped = self.implement_typechecks(all_typechecks)
        self.wrapped.extend(wrapped.keys())

        # then evaluate elements with narrowed types
        typed_dictcomp.key = self.visit(node.key)
        typed_dictcomp.value = self.visit(node.value)

        # clean up wrapped variables
        self.wrapped = [x for x in self.wrapped if x not in wrapped.keys()]

        self.exit_scope()
        typed_dictcomp.typ = InstanceType(
            DictType(typed_dictcomp.key.typ, typed_dictcomp.value.typ)
        )
        return typed_dictcomp

    def visit_FormattedValue(self, node: FormattedValue) -> TypedFormattedValue:
        typed_node = copy(node)
        typed_node.value = self.visit(node.value)
        assert node.conversion in (
            -1,
            115,
        ), "Only string formatting is allowed but got repr or ascii formatting."
        assert (
            node.format_spec is None
        ), "No format specification is allowed but got formatting specifiers (i.e. decimals)."
        typed_node.typ = StringInstanceType
        return typed_node

    def visit_JoinedStr(self, node: JoinedStr) -> TypedJoinedStr:
        typed_node = copy(node)
        typed_node.values = [self.visit(v) for v in node.values]
        typed_node.typ = StringInstanceType
        return typed_node

    def visit_ImportFrom(self, node: ImportFrom) -> ImportFrom:
        assert node.module == "opshin.bridge", "Trying to import from invalid location"
        return node

    def generic_visit(self, node: AST) -> TypedAST:
        raise NotImplementedError(
            f"Cannot infer type of non-implemented node {node.__class__}"
        )


class RecordReader(NodeVisitor):
    name: str
    orig_name: str
    constructor: typing.Optional[int]
    attributes: typing.List[typing.Tuple[str, Type]]
    _type_inferencer: AggressiveTypeInferencer

    def __init__(self, type_inferencer: AggressiveTypeInferencer):
        self.constructor = None
        self.attributes = []
        self._type_inferencer = type_inferencer

    def extract(self, c: ClassDef) -> Record:
        self.visit(c)
        if self.constructor is None:
            det_string = RecordType(
                Record(self.name, self.orig_name, 0, frozenlist(self.attributes))
            ).pluthon_type(skip_constructor=True)
            det_hash = sha256(str(det_string).encode("utf8")).hexdigest()
            self.constructor = int(det_hash, 16) % 2**32
        return Record(
            self.name, self.orig_name, self.constructor, frozenlist(self.attributes)
        )

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        assert isinstance(
            node.target, Name
        ), "Record elements must have named attributes"
        typ = self._type_inferencer.type_from_annotation(node.annotation)
        if node.target.id != "CONSTR_ID":
            assert (
                node.value is None
            ), f"PlutusData attribute {node.target.id} may not have a default value"
            assert not isinstance(
                typ, TupleType
            ), "Records can currently not hold tuples"
            self.attributes.append(
                (
                    node.target.id,
                    InstanceType(typ),
                )
            )
            return
        assert typ == IntegerType(), "CONSTR_ID must be assigned an integer"
        assert isinstance(
            node.value, Constant
        ), "CONSTR_ID must be assigned a constant integer"
        assert isinstance(
            node.value.value, int
        ), "CONSTR_ID must be assigned an integer"
        self.constructor = node.value.value

    def visit_ClassDef(self, node: ClassDef) -> None:
        self.name = node.name
        self.orig_name = node.orig_name
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
        ), "Type annotations may only be omitted for CONSTR_ID"
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
        raise NotImplementedError(f"Can not compile {ast.dump(node)} inside of a class")


def map_to_orig_name(name: str):
    return re.sub(r"_\d+$", "", name)


class ReturnExtractor(TypedNodeVisitor):
    """
    Utility to check that all paths end in Return statements with the proper type

    Returns whether there is no remaining path
    """

    def __init__(self, func_rettyp: Type):
        self.func_rettyp = func_rettyp

    def visit_sequence(self, nodes: typing.List[TypedAST]) -> bool:
        all_paths_covered = False
        for node in nodes:
            all_paths_covered = self.visit(node)
            if all_paths_covered:
                break
        return all_paths_covered

    def visit_If(self, node: If) -> bool:
        return self.visit_sequence(node.body) and self.visit_sequence(node.orelse)

    def visit_For(self, node: For) -> bool:
        # The body simply has to be checked but has no influence on whether all paths are covered
        # because it might never be visited
        self.visit_sequence(node.body)
        # the else path is always visited
        return self.visit_sequence(node.orelse)

    def visit_While(self, node: For) -> bool:
        # The body simply has to be checked but has no influence on whether all paths are covered
        # because it might never be visited
        self.visit_sequence(node.body)
        # the else path is always visited
        return self.visit_sequence(node.orelse)

    def visit_FunctionDef(self, node: FunctionDef) -> bool:
        # Nested functions are checked independently when they are inferred.
        return False

    def visit_Return(self, node: Return) -> bool:
        assert (
            self.func_rettyp >= node.typ
        ), f"Function annotated return type does not match actual return type, expected {self.func_rettyp.python_type()} but got {node.typ.python_type()}"
        return True

    def check_fulfills(self, node: FunctionDef):
        all_paths_covered = self.visit_sequence(node.body)
        if not all_paths_covered:
            assert (
                self.func_rettyp >= NoneInstanceType
            ), f"Function '{node.name}' has no return statement but is supposed to return not-None value"
