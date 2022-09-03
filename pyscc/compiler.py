from type_inference import *
import pluto_ast as plt
from enum import Enum

STATEMONAD = "s"


BinOpMap = {
    Add: {
        IntegerType: plt.BuiltInFun.AddInteger,
        ByteStringType: plt.BuiltInFun.AppendByteString,
    },
    Sub: {
        IntegerType: plt.BuiltInFun.SubtractInteger,
    },
    Mult: {
        IntegerType: plt.BuiltInFun.MultiplyInteger,
    },
    Div: {
        IntegerType: plt.BuiltInFun.DivideInteger,
    },
    Mod: {
        IntegerType: plt.BuiltInFun.RemainderInteger,
    }
}

ConstantMap = {
    str: plt.Text,
    bytes: plt.ByteString,
    int: plt.Integer,
    # TODO support higher level Optional type
    type(None): plt.Unit,
}

def extend_statemonad(names: typing.List[str], values: typing.List[plt.AST], old_statemonad: plt.AST):
    additional_compares = plt.Apply(
        old_statemonad,
        plt.Var("x")
    )
    for name, value in zip(names, values):
        additional_compares = plt.Ite(
            plt.Apply(
                plt.BuiltIn(plt.BuiltInFun.EqualsByteString),
                plt.Var("x"),
                plt.ByteString(name.encode()),
            ),
            value,
            additional_compares,
        )
    return plt.Lambda(
        ["x"],
        additional_compares,
    )

def emulate_tuple(*els: plt.AST) -> plt.AST:
    return plt.Lambda(
        ["f"],
        plt.Apply(plt.Var("f"), *els),
    )

def emulate_nth(t: plt.AST, n: int, size: int) -> plt.AST:
    return plt.Apply(t, plt.Lambda([f"v{i}" for i in range(size)], plt.Var(f"v{n}")))


class PythonBuiltIn(Enum):
    print = plt.Lambda(
        [STATEMONAD],
        plt.Lambda(
            ["x"],
            plt.Force(
                plt.Apply(
                    plt.BuiltIn(plt.BuiltInFun.Trace),
                    plt.Apply(plt.Var("x"), plt.Var(STATEMONAD)),
                    plt.Var(STATEMONAD),
                )
            )
        )
    ),
    range = plt.Lambda(
        [STATEMONAD],
        plt.Lambda(
            ["limit"],
            plt.Let([(
                    "g",
                    plt.Lambda(
                        ["state", "f", "u"],
                        emulate_tuple(
                            plt.Apply(plt.BuiltIn(plt.BuiltInFun.LessThanInteger), plt.Var("state"), plt.Var("limit")),
                            plt.Var("state"),
                            plt.Apply(plt.Var("f"), plt.Apply(plt.BuiltIn(plt.BuiltInFun.AddInteger), plt.Var("state"), plt.Integer(1)), plt.Var("f"))
                        )
                    )
                )],
                plt.Apply(plt.Var("g"), plt.Integer(0), plt.Var("g"))
            )
        )
    )

INITIAL_STATE = extend_statemonad(
    [b.name for b in PythonBuiltIn],
    [b.value for b in PythonBuiltIn],
    plt.Lambda(["x"], plt.Error()),
)


class UPLCCompiler(NodeTransformer):
    """
    Expects a TypedAST and returns UPLC/Pluto like code
    """


    def visit_sequence(self, node_seq: typing.List[typedstmt]) -> plt.AST:
        s = plt.Var(STATEMONAD)
        for n in reversed(node_seq):
            compiled_stmt = self.visit(n)
            s = plt.Apply(compiled_stmt, s)
        return plt.Lambda([STATEMONAD], s)

    def visit_BinOp(self, node: TypedBinOp) -> plt.AST:
        opmap = BinOpMap.get(type(node.op))
        if opmap is None:
            raise NotImplementedError(f"Operation {node.op} is not implemented")
        op = opmap.get(node.typ)
        if op is None:
            raise NotImplementedError(f"Operation {node.op} is not implemented for type {node.typ}")
        return plt.Lambda(
            [STATEMONAD],
            plt.Apply(
                plt.BuiltIn(op),
                plt.Apply(self.visit(node.left), plt.Var(STATEMONAD)),
                plt.Apply(self.visit(node.right), plt.Var(STATEMONAD)),
            )
        )
    
    def visit_Module(self, node: TypedModule) -> plt.AST:
        return plt.Apply(self.visit_sequence(node.body), INITIAL_STATE)

    def visit_Constant(self, node: TypedConstant) -> plt.AST:
        plt_type = ConstantMap.get(type(node.value))
        if plt_type is None:
            raise NotImplementedError(f"Constants of type {type(node.value)} are not supported")
        return plt.Lambda([STATEMONAD], plt_type(node.value))

    def visit_NoneType(self, _: typing.Optional[typing.Any]) -> plt.AST:
        return plt.Lambda([STATEMONAD], plt.Unit())

    def visit_Assign(self, node: TypedAssign) -> plt.AST:
        assert len(node.targets) == 1, "Assignments to more than one variable not supported yet"
        assert isinstance(node.targets[0], Name), "Assignments to other things then names are not supported"
        compiled_e = self.visit(node.value)
        # (\{STATEMONAD} -> (\x -> if (x ==b {self.visit(node.targets[0])}) then ({compiled_e} {STATEMONAD}) else ({STATEMONAD} x)))
        return plt.Lambda(
            [STATEMONAD],
            extend_statemonad(
                [node.targets[0].id],
                [plt.Apply(compiled_e, plt.Var(STATEMONAD))],
                plt.Var(STATEMONAD),
            )
        )

    def visit_Name(self, node: TypedName) -> plt.AST:
        # depending on load or store context, return the value of the variable or its name
        if isinstance(node.ctx, Load):
            return plt.Lambda([STATEMONAD], plt.Apply(plt.Var(STATEMONAD), plt.ByteString(node.id.encode())))
        raise NotImplementedError(f"Context {node.ctx} not supported")

    def visit_Expr(self, node: TypedExpr) -> plt.AST:
        # We can't guarantee side effects? check if this expression is evaluated
        return plt.Lambda(
            [STATEMONAD],
            plt.Apply(
                plt.Lambda(
                    ["_"],
                    plt.Var(STATEMONAD)
                ),
                self.visit(node.value),
            )
        )

    def visit_Call(self, node: TypedCall) -> plt.AST:
        # compiled_args = " ".join(f"({self.visit(a)} {STATEMONAD})" for a in node.args)
        # return rf"(\{STATEMONAD} -> ({self.visit(node.func)} {compiled_args})"
        return plt.Lambda(
            [STATEMONAD],
            plt.Apply(
                self.visit(node.func),
                *(
                    plt.Apply(
                        self.visit(a),
                        plt.Var(STATEMONAD)
                    )
                    for a in node.args
                )
            )
        )

    def visit_FunctionDef(self, node: TypedFunctionDef) -> str:
        body = node.body.copy()
        if not isinstance(body[-1], Return):
            tr = Return(None)
            tr.typ = type(None).__name__
            body.append(tr)
        compiled_body = self.visit_sequence(body[:-1])
        compiled_return = self.visit(body[-1].value)
        args_state = extend_statemonad(
            (a.arg for a in node.args.args),
            (plt.Var(f"p{i}") for i in range(len(node.args.args))),
            plt.Var(STATEMONAD),
        )
        return plt.Lambda(
            [STATEMONAD],
            plt.Lambda(
                [f"p{i}" for i in range(len(node.args.args))],
                plt.Apply(
                    compiled_return,
                    plt.Apply(
                        compiled_body,
                        args_state,
                    )
                )
            )
        )
    
    def visit_While(self, node: TypedWhile) -> plt.AST:
        compiled_c = self.cond.compile()
        compiled_s = self.stmt.compile()
        # return rf"(\{STATEMONAD} -> let g = (\s f -> if ({compiled_c} s) then f ({compiled_s} s) f else s) in (g {STATEMONAD} g))"
        return plt.Lambda(
            [STATEMONAD],
            plt.Let(
                bindings=[
                    (
                        "g",
                        plt.Lambda(
                            ["s", "f"],
                            plt.Ite(
                                plt.Apply(compiled_c, plt.Var("s")),
                                plt.Apply(plt.Var("f"), plt.Apply(compiled_s, plt.Var("s")), plt.Var("f")),
                                plt.Var("s"),
                            )
                        )
                    ),
                ],
                term=plt.Apply(plt.Var("g"), plt.Var(STATEMONAD), plt.Var("g"))
            )
        )
    
    def visit_Return(self, node: TypedReturn) -> plt.AST:
        raise NotImplementedError("Compilation of return statements except for last statement in function is not supported.")

    
    def visit_Pass(self, node: TypedPass) -> plt.AST:
        return self.visit_sequence([])
    
    def generic_visit(self, node: AST) -> str:
        raise NotImplementedError(f"Can not compile {node}")

program = """
def foo(a: int) -> int:
    return a

for a in range(4):
    print("a")

for a in [1, 2]:
    print("a")

a = 1 + 4
foo(a)
print("hi")
"""
print(dump(parse(program)))
prog = UPLCCompiler().visit(typed_ast(parse(program)))
print(prog)
print(prog.dumps())