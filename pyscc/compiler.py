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
        elif isinstance(node.op, Mult):
            if node.typ == InstanceType(int.__name__):
                op = "*i"
        elif isinstance(node.op, Div):
            if node.typ == InstanceType(int.__name__):
                op = "/i"
        if op is None:
            raise NotImplementedError("Addition for other types than int is not implemented")
        return rf"(\{STATEMONAD} -> ({self.visit(node.left)} {STATEMONAD}) {op} ({self.visit(node.right)} {STATEMONAD}))"
    
    def visit_Module(self, node: TypedModule) -> str:
        return self.visit_sequence(node.body)

    def visit_Constant(self, node: TypedConstant) -> str:
        return rf"(\{STATEMONAD} -> {str(node.value)})"

    def visit_NoneType(self, _: typing.Optional[typing.Any]) -> str:
        return rf"(\{STATEMONAD} -> None)"

    def visit_Assign(self, node: TypedAssign) -> str:
        compiled_e = self.visit(node.value)
        return rf"(\{STATEMONAD} -> (\x -> if (x ==b {self.visit(node.targets[0])}) then ({compiled_e} {STATEMONAD}) else ({STATEMONAD} x)))"

    def visit_Name(self, node: TypedName) -> str:
        # depending on load or store context, return the value of the variable or its name
        if isinstance(node.ctx, Load):
            return rf"(\{STATEMONAD} -> {STATEMONAD} 0x{node.id.encode().hex()})"
        if isinstance(node.ctx, Store):
            return rf"0x{node.id.encode().hex()}"

    def visit_Expr(self, _: TypedExpr) -> str:
        # We can't guarantee side effects, so a side-effect free expression is just ignored
        return self.visit_sequence([])

    def visit_Call(self, node: TypedCall) -> str:
        compiled_args = " ".join(f"({self.visit(a)} {STATEMONAD})" for a in node.args)
        return rf"(\{STATEMONAD} -> ({self.visit(node.func)} {compiled_args})"

    def visit_FunctionDef(self, node: TypedFunctionDef) -> str:
        body = node.body.copy()
        if not isinstance(body[-1], Return):
            tr = TypedReturn(None)
            tr.typ = type(None).__name__
            body.append(tr)
        compiled_body = self.visit_sequence(body[:-1])
        compiled_return = self.visit(body[-1].value)
        args_state = r"(\x -> "
        for i, a in enumerate(node.args.args):
            args_state += f"if (x ==b 0x{a.arg.encode().hex()}) then p{i} else ("
        args_state += f" ({STATEMONAD} x))" + len(node.args.args) * ")"
        params = "\\" + " ".join(f"p{i}" for i in range(len(node.args.args)))
        return rf"(\{STATEMONAD} -> ({params} -> {compiled_return} ({compiled_body} {args_state})))"
    
    def visit_Return(self, node: TypedReturn) -> str:
        raise NotImplementedError("Compilation of return statements except for last statement in function is not supported.")

    
    def visit_Pass(self, node: TypedPass) -> str:
        return self.visit_sequence([])
    
    def generic_visit(self, node: AST) -> str:
        raise NotImplementedError(f"Can not compile {node}")

program = """
def foo(a: int) -> int:
    return a

a = 1 + 4
foo(a)
"""
print(dump(parse(program)))
print(UPLCCompiler().visit(typed_ast(parse(program))))