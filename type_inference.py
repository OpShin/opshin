from ast import *
import typing
from dataclasses import dataclass

class Type:
    pass

@dataclass()
class BuiltinType(Type):
    typ: typing.Any

@dataclass()
class UserClassType(Type):
    name: str

@dataclass()
class TupleType(Type):
    typs: typing.List[str]

@dataclass()
class ListType(Type):
    typs: typing.List[str]


class TypedAST(AST):
    typ: Type

class typedexpr(TypedAST, expr):
    pass

class typedstmt(TypedAST, stmt):
    pass

class TypedModule(typedstmt, Module):
    body: typing.List[typedstmt]

class TypedIf(typedstmt, If):
    cond: typedexpr
    body: typing.List[typedstmt]
    orelse: typing.List[typedstmt]

class TypedExpression(typedexpr, Expression):
    body: typedexpr


class TypedAssign(typedstmt, Assign):
    targets: typing.List[typedexpr]
    value: typedexpr

class TypedName(typedexpr, Name):
    pass

class TypedConstant(TypedAST, Constant):
    pass


class TypedTuple(typedexpr, Tuple):
    typ: typing.List[TypedAST]

class TypedList(typedexpr, List):
    typ: typing.List[TypedAST]

class TypedCompare(typedexpr, Compare):
    left: typedexpr
    ops: typing.List[cmpop]
    comparators: typing.List[typedexpr]

class TypeInferenceError(AssertionError):
    pass


class AggressiveTypeInferencer(NodeTransformer):
    
    # A stack of dictionaries for storing scoped knowledge of variable types
    scopes = []

    # Obtain the type of a variable name in the current scope
    def variable_type(self, name: str):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()
    
    def set_variable_type(self, name: str, typ: Type):
        if name in self.scopes[-1] and typ != self.scopes[-1][name]:
            raise TypeInferenceError(f"Type of variable {name} in local scope does not match inferred type {typ}")
        self.scopes[-1][name] = typ

    def visit_Constant(self, node: Constant):
        tc = TypedConstant()
        assert type(node.value) not in [float, complex, type(...)], "Float, complex numbers and ellipsis currently not supported"
        tc.typ = BuiltinType(type(node.value))
        tc.value = node.value
        return tc

    
    def visit_Tuple(self, node: Tuple) -> TypedTuple:
        tt = TypedTuple()
        tt.ctx = node.ctx
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = [e.typ for e in tt.elts]
        return tt

    def visit_List(self, node: List) -> TypedList:
        tt = TypedList()
        tt.ctx = node.ctx
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = [e.typ for e in tt.elts]
        return tt
    
    def visit_Assign(self, node: Assign) -> TypedAssign:
        typed_ass = TypedAssign()
        typed_ass.typ = BuiltinType(type(None))
        typed_ass.value: TypedExpression = self.visit(node.value)
        # Make sure to first set the type of each target name so we can load it when visiting it
        for t in node.targets:
            if isinstance(t, Tuple):
                raise NotImplementedError("Type deconstruction not supported yet")
            self.set_variable_type(t.id, typed_ass.value.typ)
        typed_ass.targets = [self.visit(t) for t in node.targets]
        return typed_ass
    
    def visit_If(self, node: If) -> TypedAST:
        typed_if = TypedIf()
        typed_if.test = self.visit(node.test)
        typed_if.body = [self.visit(s) for s in node.body]
        typed_if.orelse = [self.visit(s) for s in node.orelse]
        typed_if.typ = BuiltinType(type(None))
        return typed_if
    
    def visit_Name(self, node: Name) -> TypedName:
        tn = TypedName()
        tn.id = node.id
        # Make sure that the rhs of an assign is evaluated first
        tn.typ = self.variable_type(node.id)
        return tn


    def visit_Compare(self, node: Compare) -> TypedCompare:
        typed_cmp = TypedCompare()
        typed_cmp.left = self.visit(node.left)
        typed_cmp.ops = node.ops
        typed_cmp.comparators = [self.visit(s) for s in node.comparators]
        typed_cmp.typ = BuiltinType(bool)
        assert all(typed_cmp.left.typ == c.typ for c in typed_cmp.comparators), "Not all compared expressions have the same type"
        return typed_cmp

    def visit_Module(self, node: Module) -> TypedModule:
        self.enter_scope()
        tm = TypedModule()
        tm.body = [self.visit(n) for n in node.body]
        self.exit_scope()
        return tm
    
    
    def generic_visit(self, node: AST) -> TypedAST:
        raise NotImplementedError(f"Cannot infer type of non-implemented node {node.__class__}")


print(dump(AggressiveTypeInferencer().visit(parse("""\
e = 1
if e == 0:
    a = "str"
else:
    a = "bald"
"""))))
