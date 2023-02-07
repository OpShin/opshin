from copy import copy
import ast

from .typed_ast import *
from .util import PythonBuiltInTypes, CompilingNodeTransformer

# from frozendict import frozendict


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
        if not force and name in self.scopes[-1] and typ != self.scopes[-1][name]:
            raise TypeInferenceError(
                f"Type {self.scopes[-1][name]} of variable {name} in local scope does not match inferred type {typ}"
            )
        self.scopes[-1][name] = typ

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
            assert isinstance(ann.slice, Index), "Generic types must be parameterized"
            if ann.value.id == "Union":
                assert isinstance(
                    ann.slice.value, Tuple
                ), "Union must combine multiple classes"
                ann_types = [self.type_from_annotation(e) for e in ann.slice.value.elts]
                assert all(
                    isinstance(e, RecordType) for e in ann_types
                ), "Union must combine multiple PlutusData classes"
                return UnionType(FrozenFrozenList(ann_types))
            if ann.value.id == "List":
                ann_type = self.type_from_annotation(ann.slice.value)
                assert isinstance(
                    ann_type, ClassType
                ), "List must have a single type as parameter"
                return ListType(InstanceType(ann_type))
            if ann.value.id == "Dict":
                assert isinstance(
                    ann.slice.value, Tuple
                ), "Dict must combine two classes"
                assert len(ann.slice.value.elts) == 2, "Dict must combine two classes"
                ann_types = self.type_from_annotation(
                    ann.slice.value.elts[0]
                ), self.type_from_annotation(ann.slice.value.elts[1])
                assert all(
                    isinstance(e, ClassType) for e in ann_types
                ), "Dict must combine two classes"
                return DictType(*(InstanceType(a) for a in ann_types))
            raise NotImplementedError(
                "Only Union, Dict and List are allowed as Generic types"
            )
        if ann is None:
            raise TypeInferenceError(
                "Type annotation is missing for a function argument or return value"
            )
        raise NotImplementedError(f"Annotation type {ann.__class__} is not supported")

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
        if tc.value is None:
            tc.typ = NoneInstanceType
        else:
            tc.typ = InstanceType(ATOMIC_TYPES[type(node.value).__name__])
        return tc

    def visit_Tuple(self, node: Tuple) -> TypedTuple:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = InstanceType(TupleType([e.typ for e in tt.elts]))
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
            self.set_variable_type(t.id, typed_ass.value.typ)
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
        assert typed_ass.value.typ >= InstanceType(
            typed_ass.annotation
        ), "Can only downcast to a specialized type"
        return typed_ass

    def visit_If(self, node: If) -> TypedIf:
        typed_if = copy(node)
        if (
            isinstance(typed_if.test, Call)
            and (typed_if.test.func, Name)
            and typed_if.test.func.id == "isinstance"
        ):
            tc = typed_if.test
            # special case for Union
            assert isinstance(
                tc.args[0], Name
            ), "Target 0 of an isinstance cast must be a variable name"
            assert isinstance(
                tc.args[1], Name
            ), "Target 1 of an isinstance cast must be a class name"
            target_class: RecordType = self.variable_type(tc.args[1].id)
            target_inst = self.visit(tc.args[0])
            target_inst_class = target_inst.typ
            assert isinstance(
                target_inst_class, InstanceType
            ), "Can only cast instances, not classes"
            assert isinstance(
                target_inst_class.typ, UnionType
            ), "Can only cast instances of Union types"
            assert isinstance(target_class, RecordType), "Can only cast to PlutusData"
            assert (
                target_class in target_inst_class.typ.typs
            ), f"Trying to cast an instance of Union type to non-instance of union type"
            typed_if.test = self.visit(
                Compare(
                    left=Attribute(tc.args[0], "CONSTR_ID"),
                    ops=[Eq()],
                    comparators=[Constant(target_class.record.constructor)],
                )
            )
            # for the time of this if branch set the variable type to the specialized type
            self.set_variable_type(
                tc.args[0].id, InstanceType(target_class), force=True
            )
            typed_if.body = [self.visit(s) for s in node.body]
            self.set_variable_type(tc.args[0].id, target_inst_class, force=True)
        else:
            typed_if.test = self.visit(node.test)
            assert (
                typed_if.test.typ == BoolInstanceType
            ), "Branching condition must have boolean type"
            typed_if.body = [self.visit(s) for s in node.body]
        typed_if.orelse = [self.visit(s) for s in node.orelse]
        return typed_if

    def visit_While(self, node: While) -> TypedWhile:
        typed_while = copy(node)
        typed_while.test = self.visit(node.test)
        assert (
            typed_while.test.typ == BoolInstanceType
        ), "Branching condition must have boolean type"
        typed_while.body = [self.visit(s) for s in node.body]
        typed_while.orelse = [self.visit(s) for s in node.orelse]
        return typed_while

    def visit_For(self, node: For) -> TypedFor:
        typed_for = copy(node)
        typed_for.iter = self.visit(node.iter)
        if isinstance(node.target, Tuple):
            raise NotImplementedError(
                "Type deconstruction in for loops is not supported yet"
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
        typed_for.body = [self.visit(s) for s in node.body]
        typed_for.orelse = [self.visit(s) for s in node.orelse]
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
        assert not node.decorator_list, "Functions may not have decorators"
        self.enter_scope()
        tfd.args = self.visit(node.args)
        functyp = FunctionType(
            [t.typ for t in tfd.args.args],
            InstanceType(self.type_from_annotation(tfd.returns)),
        )
        tfd.typ = InstanceType(functyp)
        # We need the function type inside for recursion
        self.set_variable_type(node.name, tfd.typ)
        tfd.body = [self.visit(s) for s in node.body]
        # Check that return type and annotated return type match
        if not isinstance(node.body[-1], Return):
            assert (
                functyp.rettyp == NoneInstanceType
            ), f"Function '{node.name}' has no return statement but is supposed to return not-None value"
        else:
            assert (
                functyp.rettyp == tfd.body[-1].typ
            ), f"Function '{node.name}' annotated return type does not match actual return type"
        self.exit_scope()
        # We need the function type outside for usage
        self.set_variable_type(node.name, tfd.typ)
        return tfd

    def visit_Module(self, node: Module) -> TypedModule:
        self.enter_scope()
        tm = copy(node)
        tm.body = [self.visit(n) for n in node.body]
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
        # TODO the outcome of the operation may depend on the input types
        assert (
            tb.left.typ == tb.right.typ
        ), "Inputs to a binary operation need to have the same type"
        tb.typ = tb.left.typ
        return tb

    def visit_BoolOp(self, node: BoolOp) -> TypedBoolOp:
        tt = copy(node)
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
            assert isinstance(
                ts.slice, Index
            ), "Only single index slices for generic types are currently supported"
            ts.value = ts.typ = self.type_from_annotation(ts)
            return ts

        ts.value = self.visit(node.value)
        assert isinstance(ts.value.typ, InstanceType), "Can only subscript instances"
        if isinstance(ts.value.typ.typ, TupleType):
            assert (
                ts.value.typ.typ.typs
            ), "Accessing elements from the empty tuple is not allowed"
            assert isinstance(
                ts.slice, Index
            ), "Only single index slices for tuples are currently supported"
            if all(ts.value.typ.typ.typs[0] == t for t in ts.value.typ.typ.typs):
                ts.typ = ts.value.typ.typ.typs[0]
            elif isinstance(ts.slice.value, Constant) and isinstance(
                ts.slice.value.value, int
            ):
                ts.typ = ts.value.typ.typ.typs[ts.slice.value.value]
            else:
                raise TypeInferenceError(
                    f"Could not infer type of subscript of typ {ts.value.typ.__class__}"
                )
        elif isinstance(ts.value.typ.typ, ListType):
            assert isinstance(
                ts.slice, Index
            ), "Only single index slices for lists are currently supported"
            ts.typ = ts.value.typ.typ.typ
            ts.slice.value = self.visit(node.slice.value)
            assert (
                ts.slice.value.typ == IntegerInstanceType
            ), "List indices must be integers"
        elif isinstance(ts.value.typ.typ, ByteStringType):
            if isinstance(ts.slice, Index):
                ts.typ = IntegerInstanceType
                ts.slice.value = self.visit(node.slice.value)
                assert (
                    ts.slice.value.typ == IntegerInstanceType
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
            raise TypeInferenceError(
                f"Could not infer type of subscript of dict. Use 'get' with a default value instead."
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
        tc.func = self.visit(node.func)
        # might be a cast
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
            ), f"Signature of function {ast.dump(node)} does not match number of arguments"
            # all arguments need to be supertypes of the given type
            assert all(
                ap >= a.typ for a, ap in zip(tc.args, functyp.argtyps)
            ), f"Signature of function {ast.dump(node)} does not match arguments"
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
        return Record(f.name, f.constructor, FrozenFrozenList(f.attributes))

    def visit_AnnAssign(self, node: AnnAssign) -> None:
        assert isinstance(
            node.target, Name
        ), "Record elements must have named attributes"
        if node.target.id != "CONSTR_ID":
            assert (
                node.value is None
            ), f"PlutusData attribute {node.target.id} may not have a default value"
            self.attributes.append(
                (
                    node.target.id,
                    InstanceType(
                        self._type_inferencer.type_from_annotation(node.annotation)
                    ),
                )
            )
            return
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
