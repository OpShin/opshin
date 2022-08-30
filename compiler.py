from type_inference import *

class UPLCCompiler(NodeTransformer):
    """
    Expects a TypedAST and returns UPLC/Pluto like code
    """

    def visit_BinOp(self, node: TypedBinOp) -> str:
        if isinstance(node.op, Add):
            if node.typ == InstanceType(int.__name__):
                return f"({self.visit(node.left)} +i {self.visit(node.right)})"
        raise NotImplementedError("Addition for other types than int is not implemented")
    
    def visit_TypedModule(self, node: TypedModule) -> str:
        return self.visit(node.body[0])

    def visit_TypedConstant(self, node: TypedConstant) -> str:
        return str(node.value)

    def visit_Expr(self, node: Expr) -> str:
        return self.visit(node.value)
    
    def generic_visit(self, node: AST) -> AST:
        raise NotImplementedError(f"Can not compile {node}")

print(
    UPLCCompiler().visit(typed_ast(parse("1 + 4")))
)