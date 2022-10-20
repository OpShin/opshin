from copy import copy
from ast import *
# from frozendict import frozendict

from .typed_ast import *

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


INITIAL_SCOPE = dict({
    "print": FunctionType([StringType], UnitType),
    "range": FunctionType(
        [IntegerType],
        TupleType([IntegerType, FunctionType([IntegerType], TupleType([BoolType, IntegerType, IntegerType]))])
    ),
    "int": FunctionType([PlutusDataType], IntegerType)
})



class AggressiveTypeInferencer(NodeTransformer):
    # TODO enforce all elements in a list to have the same type (length is not i.g. statically known!)
    
    # A stack of dictionaries for storing scoped knowledge of variable types
    scopes = [INITIAL_SCOPE]

    # Obtain the type of a variable name in the current scope
    def variable_type(self, name: str):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise TypeInferenceError(f"Variable {name} not initialized at access")
    
    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()
    
    def set_variable_type(self, name: str, typ: Type):
        if name in self.scopes[-1] and typ != self.scopes[-1][name]:
            raise TypeInferenceError(f"Type of variable {name} in local scope does not match inferred type {typ}")
        self.scopes[-1][name] = typ

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        class_record = RecordReader.extract(node)
        self.set_variable_type(node.name, ClassType(class_record))
        return node

    # TODO type inference for classDef

    def visit_Constant(self, node: Constant):
        tc = copy(node)
        assert type(node.value) not in [float, complex, type(...)], "Float, complex numbers and ellipsis currently not supported"
        tc.typ = InstanceType(type(node.value).__name__)
        return tc

    
    def visit_Tuple(self, node: Tuple) -> TypedTuple:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = TupleType([e.typ for e in tt.elts])
        return tt

    def visit_List(self, node: List) -> TypedList:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = ListType([e.typ for e in tt.elts])
        return tt
    
    def visit_Assign(self, node: Assign) -> TypedAssign:
        typed_ass = copy(node)
        typed_ass.value: TypedExpression = self.visit(node.value)
        # Make sure to first set the type of each target name so we can load it when visiting it
        for t in node.targets:
            if isinstance(t, Tuple):
                raise NotImplementedError("Type deconstruction not supported yet")
            self.set_variable_type(t.id, typed_ass.value.typ)
        typed_ass.targets = [self.visit(t) for t in node.targets]
        return typed_ass
    
    def visit_If(self, node: If) -> TypedIf:
        typed_if = copy(node)
        typed_if.test = self.visit(node.test)
        assert typed_if.test.typ == BoolType, "Branching condition must have boolean type"
        typed_if.body = [self.visit(s) for s in node.body]
        typed_if.orelse = [self.visit(s) for s in node.orelse]
        return typed_if
    
    def visit_While(self, node: While) -> TypedWhile:
        typed_while = copy(node)
        typed_while.test = self.visit(node.test)
        assert typed_while.test.typ == BoolType, "Branching condition must have boolean type"
        typed_while.body = [self.visit(s) for s in node.body]
        typed_while.orelse = [self.visit(s) for s in node.orelse]
        return typed_while

    def visit_For(self, node: For) -> TypedFor:
        typed_for = copy(node)
        typed_for.iter = self.visit(node.iter)
        if isinstance(node.target, Tuple):
            raise NotImplementedError("Type deconstruction in for loops is not supported yet")
        vartyp = None
        itertyp = typed_for.iter.typ
        if isinstance(itertyp, ListType) or isinstance(itertyp, TupleType):
            vartyp = itertyp.typs[0]
            assert all(itertyp.typs[0] == t for t in typed_for.iter.typ.typs), "Iterating through a list requires the same type for each element"
        else:
            raise NotImplementedError("Type inference for non-list objects is not supported")
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
        typed_cmp.typ = BoolType
        assert all(typed_cmp.left.typ == c.typ for c in typed_cmp.comparators), "Not all compared expressions have the same type"
        return typed_cmp
    
    def visit_arg(self, node: arg) -> typedarg:
        ta = copy(node)
        ta.typ = type_from_annotation(node.annotation)
        self.set_variable_type(ta.arg, ta.typ)
        return ta
    
    def visit_arguments(self, node: arguments) -> typedarguments:
        if node.kw_defaults or node.kwarg or node.kwonlyargs or node.defaults:
            raise NotImplementedError("Keyword arguments and defaults not supported yet")
        ta = copy(node)
        ta.args = [self.visit(a) for a in node.args]
        return ta

    
    def visit_FunctionDef(self, node: FunctionDef) -> TypedFunctionDef:
        tfd = copy(node)
        self.enter_scope()
        tfd.args = self.visit(node.args)
        tfd.typ = FunctionType(
            [t.typ for t in tfd.args.args],
            type_from_annotation(tfd.returns),
        )
        # We need the function type inside for recursion
        self.set_variable_type(node.name, tfd.typ)
        tfd.body = [self.visit(s) for s in node.body]
        # Check that return type and annotated return type match
        if not isinstance(node.body[-1], Return):
            assert tfd.typ.rettyp == UnitType, f"Function '{node.name}' has no return statement but is supposed to return not-None value"
        else:
            assert tfd.typ.rettyp == tfd.body[-1].typ, f"Function '{node.name}' annotated return type does not match actual return type"
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
        assert tb.left.typ == tb.right.typ, "Inputs to a binary operation need to have the same type"
        tb.typ = tb.left.typ
        return tb
    
    def visit_UnaryOp(self, node: UnaryOp) -> TypedUnaryOp:
        tu = copy(node)
        tu.operand = self.visit(node.operand)
        tu.typ = tu.operand.typ
        return tu

    def visit_Subscript(self, node: Subscript) -> TypedSubscript:
        ts = copy(node)
        ts.value = self.visit(node.value)
        assert isinstance(ts.slice, Index), "Only single index slices are currently supported"
        if isinstance(ts.value.typ, TupleType) or isinstance(ts.value.typ, ListType):
            if all(ts.value.typ.typs[0] == t for t in ts.value.typ.typs):
                ts.typ = ts.value.typ.typs[0]
            elif isinstance(ts.slice.value, Constant) and isinstance(ts.slice.value.value, int):
                ts.typ = ts.value.typ.typs[ts.slice.value.value]
            else:
                raise TypeInferenceError(f"Could not infer type of subscript {node}")
        else:
            raise TypeInferenceError(f"Could not infer type of subscript {node}")
        return ts
    
    def visit_Call(self, node: Call) -> TypedCall:
        assert not node.keywords, "Keyword arguments are not supported yet"
        tc = copy(node)
        tc.func = self.visit(node.func)
        tc.args = [self.visit(a) for a in node.args]
        assert len(tc.args) == len(tc.func.typ.argtyps), f"Signature of function {node} does not match number of arguments"
        assert all(a.typ == ap for a, ap in zip(tc.args, tc.func.typ.argtyps)), f"Signature of function {node} does not match arguments"
        tc.typ = tc.func.typ.rettyp
        return tc
    
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
        assert isinstance(owner, InstanceType), "Accessing attribute of non-instance"
        # look up class type in local scope
        owner_typ = self.variable_type(owner.typ)
        assert isinstance(owner_typ, ClassType), "Accessing attribute of instance of a non-class"
        tp.typ = None
        for i, (attr_name, attr_type) in enumerate(owner_typ.record.attributes):
            if attr_name == tp.attr:
                tp.typ = attr_type
                tp.pos = i
        if tp.typ is None:
            assert tp.attr in tp.value.typ.record.attributes, "Accessing undefined attribute of class-type"
        return tp

    def generic_visit(self, node: AST) -> TypedAST:
        raise NotImplementedError(f"Cannot infer type of non-implemented node {node.__class__}")


def typed_ast(ast: AST):
    return AggressiveTypeInferencer().visit(ast)