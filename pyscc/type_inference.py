from copy import copy
from ast import *
from frozendict import frozendict

from typed_ast import *


INITIAL_SCOPE = frozendict({
    "print": FunctionType([InstanceType(str.__name__)], InstanceType(str.__name__))
})


class TypeInferenceError(AssertionError):
    pass

def type_from_annotation(ann: expr):
    if isinstance(ann, Constant):
        if ann.value is None:
            return InstanceType(type(None).__name__)
    if isinstance(ann, Name):
        return InstanceType(ann.id)
    if isinstance(ann, Subscript):
        raise NotImplementedError("Generic types not supported yet")
    raise NotImplementedError(f"Annotation type {ann} is not supported")


class AggressiveTypeInferencer(NodeTransformer):
    
    # A stack of dictionaries for storing scoped knowledge of variable types
    scopes = [INITIAL_SCOPE]

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
        tc = copy(node)
        assert type(node.value) not in [float, complex, type(...)], "Float, complex numbers and ellipsis currently not supported"
        tc.typ = InstanceType(type(node.value).__name__)
        return tc

    
    def visit_Tuple(self, node: Tuple) -> TypedTuple:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = [e.typ for e in tt.elts]
        return tt

    def visit_List(self, node: List) -> TypedList:
        tt = copy(node)
        tt.elts = [self.visit(e) for e in node.elts]
        tt.typ = [e.typ for e in tt.elts]
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
    
    def visit_If(self, node: If) -> TypedAST:
        typed_if = copy(node)
        typed_if.test = self.visit(node.test)
        typed_if.body = [self.visit(s) for s in node.body]
        typed_if.orelse = [self.visit(s) for s in node.orelse]
        return typed_if
    
    def visit_Name(self, node: Name) -> TypedName:
        tn = copy(node)
        # Make sure that the rhs of an assign is evaluated first
        tn.typ = self.variable_type(node.id)
        return tn


    def visit_Compare(self, node: Compare) -> TypedCompare:
        typed_cmp = copy(node)
        typed_cmp.left = self.visit(node.left)
        typed_cmp.comparators = [self.visit(s) for s in node.comparators]
        typed_cmp.typ = InstanceType(bool.__name__)
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
    
    def visit_Call(self, node: Call) -> TypedCall:
        assert not node.keywords, "Keyword arguments are not supported yet"
        tc = copy(node)
        tc.func = self.visit(node.func)
        tc.args = [self.visit(a) for a in node.args]
        assert all(a.typ == ap for a, ap in zip(tc.args, tc.func.typ.argtyps))
        tc.typ = tc.func.typ.rettyp
        return tc
    
    def visit_Pass(self, node: Pass) -> TypedPass:
        tp = copy(node)
        return tp

    def visit_Return(self, node: Return) -> TypedReturn:
        tp = copy(node)
        tp.value = self.visit(node.value)
        return tp
    
    def generic_visit(self, node: AST) -> TypedAST:
        raise NotImplementedError(f"Cannot infer type of non-implemented node {node.__class__}")


def typed_ast(ast: AST):
    return AggressiveTypeInferencer().visit(ast)