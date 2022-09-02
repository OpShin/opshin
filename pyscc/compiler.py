from type_inference import *

STATEMONAD = "s"

class UPLCCompiler(NodeTransformer):
    """
    Expects a TypedAST and returns UPLC/Pluto like code
    """

    def visit_sequence(self, node_seq: typing.List[typedstmt]):
        s = STATEMONAD
        for n in reversed(node_seq):
            compiled_stmt = self.visit(n)
            s = f"({compiled_stmt} {s})"
        return rf"(\{STATEMONAD} -> {s})"

    def visit_BinOp(self, node: TypedBinOp) -> str:
        op = None
        if isinstance(node.op, Add):
            if node.typ == InstanceType(int.__name__):
                op = "+i"
        elif isinstance(node.op, Sub):
            if node.typ == InstanceType(int.__name__):
                op = "-i"
        elif isinstance(node.op, Mul):
            if node.typ == InstanceType(int.__name__):
                op = "*i"
        if op is None:
            raise NotImplementedError("Addition for other types than int is not implemented")
        return rf"(\{STATEMONAD} -> ({self.visit(node.left)} {STATEMONAD}) {op} ({self.visit(node.right)} {STATEMONAD}))"
    
    def visit_Module(self, node: TypedModule) -> str:
        return self.visit_sequence(node.body)

    def visit_Constant(self, node: TypedConstant) -> str:
        return rf"(\{STATEMONAD} -> {str(node.value)})"

    def visit_Assign(self, node: TypedAssign) -> str:
        compiled_e = self.visit(node.value)
        return rf"(\{STATEMONAD} -> (\x -> if (x ==b {self.visit(node.targets[0])}) then ({compiled_e} {STATEMONAD}) else ({STATEMONAD} x)))"

    def visit_Name(self, node: TypedName) -> str:
        # depending on load or store context, return the value of the variable or its name
        if isinstance(node.ctx, Load):
            return rf"(\{STATEMONAD} -> {STATEMONAD} 0x{node.id.encode().hex()})"
        if isinstance(node.ctx, Store):
            return rf"0x{node.id.encode().hex()}"

    def visit_Expr(self, node: TypedExpr) -> str:
        return self.visit(node.value)

    def visit_Call(self, node: TypedCall) -> str:
        compiled_args = " ".join(f"({self.visit(a)} {STATEMONAD})" for a in node.args)
        return rf"(\{STATEMONAD} -> ({self.visit(node.func)} {compiled_args})"

    def visit_FunctionDef(self, node: TypedFunctionDef) -> str:
        compiled_args = " ".join(f"({self.visit(a)} {STATEMONAD})" for a in node.args)
        return rf"(\{STATEMONAD} -> ({self.visit(node.func)} {compiled_args})"
    
    def visit_Pass(self) -> str:
        return self.visit_sequence([])
    
    def generic_visit(self, node: AST) -> str:
        raise NotImplementedError(f"Can not compile {node}")

print(
    UPLCCompiler().visit(typed_ast(parse("""
def foo(a: int) -> None:
    pass

a = 1 + 4
foo(a)
""")))
)