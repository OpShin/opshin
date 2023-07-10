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
import typing
from collections import defaultdict

from copy import copy
from pycardano import PlutusData
from logging import getLogger

from .typed_ast import *
from .util import CompilingNodeTransformer
from .fun_impls import PythonBuiltInTypes
from .rewrite.rewrite_cast_condition import SPECIAL_BOOL

# from frozendict import frozendict

_LOGGER = logging.getLogger(__name__)


INITIAL_SCOPE = dict(
    {
        # class annotations
        "bytes": ByteStringType(),
        "int": IntegerType(),
        "bool": BoolType(),
        "str": StringType(),
        "Anything": AnyType(),
    }
)

INITIAL_SCOPE.update(
    {
        name.name: typ
        for name, typ in PythonBuiltInTypes.items()
        if isinstance(typ.typ, PolymorphicFunctionType)
    }
)


def record_from_plutusdata(c: PlutusData):
    return Record(
        name=c.__class__.__name__,
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
        first_typ = constant_type(c[0])
        assert all(
            constant_type(ce) == first_typ for ce in c[1:]
        ), "Constant lists must contain elements of a single type only"
        return InstanceType(ListType(first_typ))
    if isinstance(c, dict):
        assert len(c) > 0, "Lists must be non-empty"
        first_key_typ = constant_type(next(iter(c.keys())))
        first_value_typ = constant_type(next(iter(c.values())))
        assert all(
            constant_type(ce) == first_key_typ for ce in c.keys()
        ), "Constant dicts must contain keys of a single type only"
        assert all(
            constant_type(ce) == first_value_typ for ce in c.values()
        ), "Constant dicts must contain values of a single type only"
        return InstanceType(DictType(first_key_typ, first_value_typ))
    if isinstance(c, PlutusData):
        return InstanceType(RecordType(record=record_from_plutusdata(c)))
    raise NotImplementedError(f"Type {type(c)} not supported")


BinOpTypeMap = {
    Add: {
        IntegerInstanceType: {
            IntegerInstanceType: IntegerInstanceType,
        },
        ByteStringInstanceType: {
            ByteStringInstanceType: ByteStringInstanceType,
        },
        StringInstanceType: {
            StringInstanceType: StringInstanceType,
        },
    },
    Sub: {
        IntegerInstanceType: {
            IntegerInstanceType: IntegerInstanceType,
        }
    },
    Mult: {
        IntegerInstanceType: {
            IntegerInstanceType: IntegerInstanceType,
            ByteStringInstanceType: ByteStringInstanceType,
            StringInstanceType: StringInstanceType,
        },
        StringInstanceType: {
            IntegerInstanceType: StringInstanceType,
        },
        ByteStringInstanceType: {
            IntegerInstanceType: ByteStringInstanceType,
        },
    },
    FloorDiv: {
        IntegerInstanceType: {
            IntegerInstanceType: IntegerInstanceType,
        }
    },
    Mod: {
        IntegerInstanceType: {
            IntegerInstanceType: IntegerInstanceType,
        }
    },
    Pow: {
        IntegerInstanceType: {
            IntegerInstanceType: IntegerInstanceType,
        }
    },
}


TypeMap = typing.Dict[str, Type]
TypeMapPair = typing.Tuple[TypeMap, TypeMap]


def union_types(*ts: Type):
    ts = list(set(ts))
    if len(ts) == 1:
        return ts[0]
    assert ts, "Union must combine multiple classes"
    ts = [t if isinstance(t, UnionType) else UnionType(frozenlist([t])) for t in ts]
    assert all(
        isinstance(e, UnionType) and all(isinstance(e2, RecordType) for e2 in e.typs)
        for e in ts
    ), "Union must combine multiple PlutusData classes"
    union_set = set()
    for t in ts:
        union_set.update(t.typs)
    assert distinct(
        [e.record.constructor for e in union_set]
    ), "Union must combine PlutusData classes with unique constructors"
    return UnionType(frozenlist(union_set))


def intersection_types(*ts: Type):
    ts = list(set(ts))
    if len(ts) == 1:
        return ts[0]
    ts = [t if isinstance(t, UnionType) else UnionType(frozenlist([t])) for t in ts]
    assert ts, "Must have at least one type to intersect"
    intersection_set = set(ts[0].typs)
    for t in ts[1:]:
        intersection_set.intersection_update(t.typs)
    return UnionType(frozenlist(intersection_set))


class TypeCheckVisitor(TypedNodeVisitor):
    """
    Generates the types to which objects are cast due to a boolean expression
    It returns a tuple of dictionaries which are a name -> type mapping
    for variable names that are assured to have a specific type if this expression
    is True/False respectively
    """

    def generic_visit(self, node: AST) -> TypeMapPair:
        return getattr(node, "typechecks", ({}, {}))

    def visit_Call(self, node: Call) -> TypeMapPair:
        if isinstance(node.func, Name) and node.func.id == SPECIAL_BOOL:
            return self.visit(node.args[0])
        if not (isinstance(node.func, Name) and node.func.id == "isinstance"):
            return ({}, {})
        # special case for Union
        assert isinstance(
            node.args[0], Name
        ), "Target 0 of an isinstance cast must be a variable name"
        assert isinstance(
            node.args[1], Name
        ), "Target 1 of an isinstance cast must be a class name"
        target_class: RecordType = node.args[1].typ
        target_inst = node.args[0]
        target_inst_class = target_inst.typ
        assert isinstance(
            target_inst_class, InstanceType
        ), "Can only cast instances, not classes"
        assert isinstance(target_class, RecordType), "Can only cast to PlutusData"
        if isinstance(target_inst_class.typ, UnionType):
            assert (
                target_class in target_inst_class.typ.typs
            ), f"Trying to cast an instance of Union type to non-instance of union type"
            union_without_target_class = union_types(
                *(x for x in target_inst_class.typ.typs if x != target_class)
            )
        else:
            assert (
                target_inst_class.typ == target_class
            ), "Can only cast instances of Union types of PlutusData or cast the same class"
            union_without_target_class = target_class
        varname = node.args[0].id
        return ({varname: target_class}, {varname: union_without_target_class})

    def visit_BoolOp(self, node: BoolOp) -> PairType:
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
        if isinstance(node.op, Or):
            # a disjunction is just the union, but some type must be checked in every disjunction
            for v, ts in checked_types.items():
                if len(ts) < len(checks):
                    continue
                res[v] = union_types(*ts)
            # if the disjunction fails, then it must be in the intersection of the inverses
            for v, ts in inv_checked_types.items():
                inv_res[v] = intersection_types(*ts)
        return (res, inv_res)

    def visit_UnaryOp(self, node: UnaryOp) -> PairType:
        (res, inv_res) = self.visit(node.operand)
        if isinstance(node.op, Not):
            return (inv_res, res)
        return (res, inv_res)


def merge_scope(s1: typing.Dict[str, Type], s2: typing.Dict[str, Type]):
    keys = set(s1.keys()).union(s2.keys())
    merged = {}
    for k in keys:
        if k not in s1.keys():
            merged[k] = s2[k]
        elif k not in s2.keys():
            merged[k] = s1[k]
        else:
            try:
                assert (
                    isinstance(s1[k], InstanceType) and isinstance(s2[k], InstanceType)
                ) or s1[k] == s2[
                    k
                ], "Can only merge instance types or same types into one"
                merged[k] = InstanceType(union_types(s1[k].typ, s2[k].typ))
            except AssertionError as e:
                raise AssertionError(
                    f"Can not merge scopes after branching, conflicting types for {k}: {e}"
                )
    return merged


class AggressiveTypeInferencer(CompilingNodeTransformer):
    step = "Static Type Inference"

    # A stack of dictionaries for storing scoped knowledge of variable types
    scopes = [INITIAL_SCOPE]

    # Obtain the type of a variable name in the current scope
    def variable_type(self, name: str) -> Type:
        name = name
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise TypeInferenceError(f"Variable {name} not initialized at access")

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
                f"Type {self.scopes[-1][name]} of variable {name} in local scope does not match inferred type {typ}"
            )
        self.scopes[-1][name] = typ

    def implement_typechecks(self, typchecks: TypeMap):
        prevtyps = {}
        for n, t in typchecks.items():
            prevtyps[n] = self.variable_type(n).typ
            self.set_variable_type(n, InstanceType(t), force=True)
        return prevtyps

    def type_from_annotation(self, ann: expr):
        if isinstance(ann, Constant):
            if ann.value is None:
                return UnitType()
        if isinstance(ann, Name):
            if ann.id in ATOMIC_TYPES:
                return ATOMIC_TYPES[ann.id]
            v_t = self.variable_type(ann.id)
            if isinstance(v_t, ClassType):
                return v_t
            raise TypeInferenceError(
                f"Class name {ann.id} not initialized before annotating variable"
            )
        if isinstance(ann, Subscript):
            assert isinstance(
                ann.value, Name
            ), "Only Union, Dict and List are allowed as Generic types"
            if ann.value.id == "Union":
                ann_types = frozenlist(
                    [self.type_from_annotation(e) for e in ann.slice.elts]
                )
                return union_types(*ann_types)
            if ann.value.id == "List":
                ann_type = self.type_from_annotation(ann.slice)
                assert isinstance(
                    ann_type, ClassType
                ), "List must have a single type as parameter"
                assert not isinstance(
                    ann_type, TupleType
                ), "List can currently not hold tuples"
                return ListType(InstanceType(ann_type))
            if ann.value.id == "Dict":
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
            if ann.value.id == "Tuple":
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

    def visit_sequence(self, node_seq: typing.List[stmt]) -> plt.AST:
        stmts = []
        prevtyps = {}
        for n in node_seq:
            stmt = self.visit(n)
            stmts.append(stmt)
            # if an assert is amng the statements apply the isinstance cast
            if isinstance(stmt, Assert):
                typchecks, _ = TypeCheckVisitor().visit(stmt.test)
                # for the time after this assert, the variable has the specialized type
                prevtyps.update(self.implement_typechecks(typchecks))
        self.implement_typechecks(prevtyps)
        return stmts

    def visit_ClassDef(self, node: ClassDef) -> TypedClassDef:
        class_record = RecordReader.extract(node, self)
        typ = RecordType(class_record)
        self.set_variable_type(node.name, typ)
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

    def visit_Tuple(self, node: Tuple) -> TypedTuple:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = InstanceType(TupleType(frozenlist([e.typ for e in tt.elts])))
        return tt

    def visit_List(self, node: List) -> TypedList:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        l_typ = tt.elts[0].typ
        assert all(
            l_typ >= e.typ for e in tt.elts
        ), "All elements of a list must have the same type"
        tt.typ = InstanceType(ListType(l_typ))
        return tt

    def visit_Dict(self, node: Dict) -> TypedDict:
        tt = copy(node)
        tt.keys = [self.visit(k) for k in node.keys]
        tt.values = [self.visit(v) for v in node.values]
        k_typ = tt.keys[0].typ
        assert all(k_typ >= k.typ for k in tt.keys), "All keys must have the same type"
        v_typ = tt.values[0].typ
        assert all(
            v_typ >= v.typ for v in tt.values
        ), "All values must have the same type"
        tt.typ = InstanceType(DictType(k_typ, v_typ))
        return tt

    def visit_Assign(self, node: Assign) -> TypedAssign:
        typed_ass = copy(node)
        typed_ass.value: TypedExpression = self.visit(node.value)
        # Make sure to first set the type of each target name so we can load it when visiting it
        for t in node.targets:
            assert isinstance(
                t, Name
            ), "Can only assign to variable names, no type deconstruction"
            # Overwrite previous type -> this will only affect following statements
            self.set_variable_type(t.id, typed_ass.value.typ, force=True)
        typed_ass.targets = [self.visit(t) for t in node.targets]
        return typed_ass

    def visit_AnnAssign(self, node: AnnAssign) -> TypedAnnAssign:
        typed_ass = copy(node)
        typed_ass.value: TypedExpression = self.visit(node.value)
        typed_ass.annotation = self.type_from_annotation(node.annotation)
        assert isinstance(
            node.target, Name
        ), "Can only assign to variable names, no type deconstruction"
        self.set_variable_type(
            node.target.id, InstanceType(typed_ass.annotation), force=True
        )
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
        typchecks, inv_typchecks = TypeCheckVisitor().visit(typed_if.test)
        # for the time of the branch, these types are cast
        initial_scope = copy(self.scopes[-1])
        self.implement_typechecks(typchecks)
        typed_if.body = self.visit_sequence(node.body)
        # save resulting types
        final_scope_body = copy(self.scopes[-1])
        # reverse typechecks and remove typing of one branch
        self.scopes[-1] = initial_scope
        # for the time of the else branch, the inverse types hold
        self.implement_typechecks(inv_typchecks)
        typed_if.orelse = self.visit_sequence(node.orelse)
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
        typchecks, inv_typchecks = TypeCheckVisitor().visit(typed_while.test)
        # for the time of the branch, these types are cast
        initial_scope = copy(self.scopes[-1])
        self.implement_typechecks(typchecks)
        typed_while.body = self.visit_sequence(node.body)
        final_scope_body = copy(self.scopes[-1])
        # revert changes
        self.scopes[-1] = initial_scope
        # for the time of the else branch, the inverse types hold
        self.implement_typechecks(inv_typchecks)
        typed_while.orelse = self.visit_sequence(node.orelse)
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
                itertyp.typ.typs[0] == t for t in typed_for.iter.typ.typs
            ), "Iterating through a tuple requires the same type for each element"
        elif isinstance(itertyp.typ, ListType):
            vartyp = itertyp.typ.typ
        else:
            raise NotImplementedError(
                "Type inference for loops over non-list objects is not supported"
            )
        self.set_variable_type(node.target.id, vartyp)
        typed_for.target = self.visit(node.target)
        typed_for.body = self.visit_sequence(node.body)
        typed_for.orelse = self.visit_sequence(node.orelse)
        return typed_for

    def visit_Name(self, node: Name) -> TypedName:
        tn = copy(node)
        # Make sure that the rhs of an assign is evaluated first
        tn.typ = self.variable_type(node.id)
        return tn

    def visit_Compare(self, node: Compare) -> TypedCompare:
        typed_cmp = copy(node)
        typed_cmp.left = self.visit(node.left)
        typed_cmp.comparators = [self.visit(s) for s in node.comparators]
        typed_cmp.typ = BoolInstanceType
        # the actual required types are being taken care of in the implementation
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
        tfd = copy(node)
        wraps_builtin = (
            all(
                isinstance(o, Name) and o.id == "wraps_builtin"
                for o in node.decorator_list
            )
            and node.decorator_list
        )
        assert (
            not node.decorator_list or wraps_builtin
        ), "Functions may not have decorators other than wraps_builtin"
        self.enter_scope()
        tfd.args = self.visit(node.args)
        functyp = FunctionType(
            frozenlist([t.typ for t in tfd.args.args]),
            InstanceType(self.type_from_annotation(tfd.returns)),
        )
        tfd.typ = InstanceType(functyp)
        if wraps_builtin:
            # the body of wrapping builtin functions is fully ignored
            pass
        else:
            # We need the function type inside for recursion
            self.set_variable_type(node.name, tfd.typ)
            tfd.body = self.visit_sequence(node.body)
            # Check that return type and annotated return type match
            if not isinstance(node.body[-1], Return):
                assert (
                    functyp.rettyp >= NoneInstanceType
                ), f"Function '{node.name}' has no return statement but is supposed to return not-None value"
            else:
                assert (
                    functyp.rettyp >= tfd.body[-1].typ
                ), f"Function '{node.name}' annotated return type does not match actual return type"

        self.exit_scope()
        # We need the function type outside for usage
        self.set_variable_type(node.name, tfd.typ)
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

    def visit_BinOp(self, node: BinOp) -> TypedBinOp:
        tb = copy(node)
        tb.left = self.visit(node.left)
        tb.right = self.visit(node.right)
        outcome_typ_map = BinOpTypeMap.get(type(node.op)).get(tb.left.typ)
        assert (
            outcome_typ_map is not None
        ), f"Operation {node.op} not defined for {tb.left.typ}"
        outcome_typ = outcome_typ_map.get(tb.right.typ)
        assert (
            outcome_typ is not None
        ), f"Operation {node.op} not defined for types {tb.left.typ} and {tb.right.typ}"
        tb.typ = outcome_typ
        return tb

    def visit_BoolOp(self, node: BoolOp) -> TypedBoolOp:
        tt = copy(node)
        if isinstance(node.op, And):
            values = []
            prevtyps = {}
            for e in node.values:
                values.append(self.visit(e))
                typchecks, _ = TypeCheckVisitor().visit(values[-1])
                # for the time after the shortcut and the variable type to the specialized type
                prevtyps.update(self.implement_typechecks(typchecks))
            self.implement_typechecks(prevtyps)
            tt.values = values
        elif isinstance(node.op, Or):
            values = []
            prevtyps = {}
            for e in node.values:
                values.append(self.visit(e))
                _, inv_typechecks = TypeCheckVisitor().visit(values[-1])
                # for the time after the shortcut or the variable type is *not* the specialized type
                prevtyps.update(self.implement_typechecks(inv_typechecks))
            self.implement_typechecks(prevtyps)
            tt.values = values
        else:
            tt.values = [self.visit(e) for e in node.values]
        tt.typ = BoolInstanceType
        assert all(
            BoolInstanceType >= e.typ for e in tt.values
        ), "All values compared must be bools"
        return tt

    def visit_UnaryOp(self, node: UnaryOp) -> TypedUnaryOp:
        tu = copy(node)
        tu.operand = self.visit(node.operand)
        tu.typ = tu.operand.typ
        return tu

    def visit_Subscript(self, node: Subscript) -> TypedSubscript:
        ts = copy(node)
        # special case: Subscript of Union / Dict / List and atomic types
        if isinstance(ts.value, Name) and ts.value.id in [
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
            if all(ts.value.typ.typ.typs[0] == t for t in ts.value.typ.typ.typs):
                ts.typ = ts.value.typ.typ.typs[0]
            elif isinstance(ts.slice, Constant) and isinstance(ts.slice.value, int):
                ts.typ = ts.value.typ.typ.typs[ts.slice.value]
            else:
                raise TypeInferenceError(
                    f"Could not infer type of subscript of typ {ts.value.typ.typ.__class__}"
                )
        elif isinstance(ts.value.typ.typ, PairType):
            if isinstance(ts.slice, Constant) and isinstance(ts.slice.value, int):
                ts.typ = (
                    ts.value.typ.typ.l_typ
                    if ts.slice.value == 0
                    else ts.value.typ.typ.r_typ
                )
            else:
                raise TypeInferenceError(
                    f"Could not infer type of subscript of typ {ts.value.typ.typ.__class__}"
                )
        elif isinstance(ts.value.typ.typ, ListType):
            ts.typ = ts.value.typ.typ.typ
            ts.slice = self.visit(node.slice)
            assert ts.slice.typ == IntegerInstanceType, "List indices must be integers"
        elif isinstance(ts.value.typ.typ, ByteStringType):
            if not isinstance(ts.slice, Slice):
                ts.typ = IntegerInstanceType
                ts.slice = self.visit(node.slice)
                assert (
                    ts.slice.typ == IntegerInstanceType
                ), "bytes indices must be integers"
            elif isinstance(ts.slice, Slice):
                ts.typ = ByteStringInstanceType
                if ts.slice.lower is None:
                    ts.slice.lower = Constant(0)
                ts.slice.lower = self.visit(node.slice.lower)
                assert (
                    ts.slice.lower.typ == IntegerInstanceType
                ), "lower slice indices for bytes must be integers"
                if ts.slice.upper is None:
                    ts.slice.upper = Call(
                        func=Name(id="len", ctx=Load()), args=[ts.value], keywords=[]
                    )
                ts.slice.upper = self.visit(node.slice.upper)
                assert (
                    ts.slice.upper.typ == IntegerInstanceType
                ), "upper slice indices for bytes must be integers"
            else:
                raise TypeInferenceError(
                    f"Could not infer type of subscript of typ {ts.value.typ.__class__}"
                )
        elif isinstance(ts.value.typ.typ, DictType):
            # TODO could be implemented with potentially just erroring. It might be desired to avoid this though.
            if not isinstance(ts.slice, Slice):
                ts.slice = self.visit(node.slice)
                assert (
                    ts.slice.typ == ts.value.typ.typ.key_typ
                ), f"Dict subscript must have dict key type {ts.value.typ.typ.key_typ} but has type {ts.slice.typ}"
                ts.typ = ts.value.typ.typ.value_typ
            else:
                raise TypeInferenceError(
                    f"Could not infer type of subscript of dict with a slice."
                )
        else:
            raise TypeInferenceError(
                f"Could not infer type of subscript of typ {ts.value.typ.__class__}"
            )
        return ts

    def visit_Call(self, node: Call) -> TypedCall:
        assert not node.keywords, "Keyword arguments are not supported yet"
        tc = copy(node)
        tc.args = [self.visit(a) for a in node.args]
        # might be isinstance
        if isinstance(tc.func, Name) and tc.func.id == "isinstance":
            target_class = tc.args[1].typ
            ntc = self.visit(
                Compare(
                    left=Attribute(tc.args[0], "CONSTR_ID"),
                    ops=[Eq()],
                    comparators=[Constant(target_class.record.constructor)],
                )
            )
            ntc.typ = BoolInstanceType
            ntc.typechecks = TypeCheckVisitor().visit(tc)
            return ntc
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
            ), f"Signature of function does not match number of arguments. Expected {len(functyp.argtyps)} arguments with these types: {functyp.argtyps} but got {len(tc.args)} arguments."
            # all arguments need to be supertypes of the given type
            assert all(
                ap >= a.typ for a, ap in zip(tc.args, functyp.argtyps)
            ), f"Signature of function does not match arguments. Expected {len(functyp.argtyps)} arguments with these types: {functyp.argtyps} but got {[a.typ for a in tc.args]}."
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
        typchecks, inv_typchecks = TypeCheckVisitor().visit(node_cp.test)
        prevtyps = self.implement_typechecks(typchecks)
        node_cp.body = self.visit(node.body)
        self.implement_typechecks(prevtyps)
        prevtyps = self.implement_typechecks(inv_typchecks)
        node_cp.orelse = self.visit(node.orelse)
        self.implement_typechecks(prevtyps)
        if node_cp.body.typ >= node_cp.orelse.typ:
            node_cp.typ = node_cp.body.typ
        elif node_cp.orelse.typ >= node_cp.body.typ:
            node_cp.typ = node_cp.orelse.typ
        else:
            raise TypeInferenceError(
                "Branches of if-expression must return compatible types"
            )
        return node_cp

    def visit_comprehension(self, g: comprehension) -> typedcomprehension:
        new_g = copy(g)
        if isinstance(g.target, Tuple):
            raise NotImplementedError(
                "Type deconstruction in for loops is not supported yet"
            )
        new_g.iter = self.visit(g.iter)
        itertyp = new_g.iter.typ
        assert isinstance(
            itertyp, InstanceType
        ), "Can only iterate over instances, not classes"
        if isinstance(itertyp.typ, TupleType):
            assert itertyp.typ.typs, "Iterating over an empty tuple is not allowed"
            vartyp = itertyp.typ.typs[0]
            assert all(
                itertyp.typ.typs[0] == t for t in new_g.iter.typ.typs
            ), "Iterating through a tuple requires the same type for each element"
        elif isinstance(itertyp.typ, ListType):
            vartyp = itertyp.typ.typ
        else:
            raise NotImplementedError(
                "Type inference for loops over non-list objects is not supported"
            )
        self.set_variable_type(g.target.id, vartyp)
        new_g.target = self.visit(g.target)
        new_g.ifs = [self.visit(i) for i in g.ifs]
        return new_g

    def visit_ListComp(self, node: ListComp) -> TypedListComp:
        typed_listcomp = copy(node)
        # inside the comprehension is a seperate scope
        self.enter_scope()
        # first evaluate generators for assigned variables
        typed_listcomp.generators = [self.visit(s) for s in node.generators]
        # then evaluate elements
        typed_listcomp.elt = self.visit(node.elt)
        self.exit_scope()
        typed_listcomp.typ = InstanceType(ListType(typed_listcomp.elt.typ))
        return typed_listcomp

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
    constructor: int
    attributes: typing.List[typing.Tuple[str, Type]]
    _type_inferencer: AggressiveTypeInferencer

    def __init__(self, type_inferencer: AggressiveTypeInferencer):
        self.constructor = 0
        self.attributes = []
        self._type_inferencer = type_inferencer

    @classmethod
    def extract(cls, c: ClassDef, type_inferencer: AggressiveTypeInferencer) -> Record:
        f = cls(type_inferencer)
        f.visit(c)
        return Record(f.name, f.constructor, frozenlist(f.attributes))

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
        assert typ == IntegerType, "CONSTR_ID must be assigned an integer"
        assert isinstance(
            node.value, Constant
        ), "CONSTR_ID must be assigned a constant integer"
        assert isinstance(
            node.value.value, int
        ), "CONSTR_ID must be assigned an integer"
        self.constructor = node.value.value

    def visit_ClassDef(self, node: ClassDef) -> None:
        self.name = node.name
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


def typed_ast(ast: AST):
    return AggressiveTypeInferencer().visit(ast)
