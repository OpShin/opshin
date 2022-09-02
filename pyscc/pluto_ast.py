import enum
from dataclasses import dataclass
import typing

from uplc_ast import AST as UPLCAst, BuiltInFun
import uplc_ast


class AST:
    def compile(self) -> UPLCAst:
        raise NotImplementedError()

    def dumps(self) -> str:
        raise NotImplementedError()


@dataclass
class Var(AST):
    name: str

    def compile(self):
        return uplc_ast.Variable(self.name)

    def dumps(self) -> str:
        return self.name


@dataclass
class Lambda(AST):
    vars: typing.List[str]
    term: AST

    def compile(self):
        if not self.vars:
            raise RuntimeError("Invalid lambda without variables")
        t = self.term.compile()
        varscp = self.vars.copy()
        while varscp:
            t = uplc_ast.Lambda(varscp.pop(), t)
        return t

    def dumps(self) -> str:
        return f"(\\{' '.join(self.vars)} -> {self.term.dumps()}"


@dataclass
class Apply(AST):
    f: AST
    x: AST

    def compile(self):
        return uplc_ast.Apply(self.f.compile(), self.x.compile())

    def dumps(self) -> str:
        return f"({self.f.dumps()} {self.x.dumps()})"


@dataclass
class Force(AST):
    x: AST

    def compile(self):
        return uplc_ast.Force(self.x.compile())

    def dumps(self) -> str:
        return f"(! {self.x.dumps()})"


@dataclass
class Delay(AST):
    x: AST

    def compile(self):
        return uplc_ast.Delay(self.x.compile())

    def dumps(self) -> str:
        return f"(# {self.x.dumps()})"


@dataclass
class Integer(AST):
    x: int

    def compile(self):
        return uplc_ast.Constant(uplc_ast.ConstantType.integer, str(self.x))

    def dumps(self) -> str:
        return str(self.x)


@dataclass
class ByteString(AST):
    x: bytes

    def compile(self):
        return uplc_ast.Constant(uplc_ast.ConstantType.bytestring, f"#{self.x.hex()}")

    def dumps(self) -> str:
        return f"0x{self.x.hex()}"


@dataclass
class Text(AST):
    x: str

    def compile(self):
        return uplc_ast.Constant(
            uplc_ast.ConstantType.bytestring, f"#{self.x.encode('utf8').hex()}"
        )

    def dumps(self) -> str:
        return f'"{self.x}"'


@dataclass
class Bool(AST):
    x: bool

    def compile(self):
        return uplc_ast.Constant(
            uplc_ast.ConstantType.bool, "True" if self.x else "False"
        )

    def dumps(self) -> str:
        return "True" if self.x else "False"


@dataclass
class BuiltIn(AST):
    builtin: BuiltInFun

    def compile(self):
        return uplc_ast.BuiltIn(self.builtin)

    def dumps(self) -> str:
        return f"{self.builtin.name}"


@dataclass
class Error(AST):
    def compile(self):
        return uplc_ast.Error()

    def dumps(self) -> str:
        return "(Error ())"


@dataclass
class Let(AST):
    bindings: typing.List[typing.Tuple[str, AST]]
    term: AST

    def compile(self):
        t = self.term.compile()
        bindingscp = self.bindings.copy()
        while bindingscp:
            (b_name, b_term) = bindingscp.pop()
            t = uplc_ast.Apply(
                uplc_ast.Lambda(b_name, t),
                b_term.compile(),
            )
        return t

    def dumps(self) -> str:
        bindingss = ";".join(
            f"{b_name} = {b_term.dumps()}" for b_name, b_term in self.bindings
        )
        return f"(let {bindingss} in {self.term.dumps()})"


@dataclass
class Ite(AST):
    i: AST
    t: AST
    e: AST

    def compile(self):
        return uplc_ast.Force(
            uplc_ast.Apply(
                uplc_ast.Apply(
                    uplc_ast.Apply(
                        uplc_ast.Force(
                            uplc_ast.BuiltIn(uplc_ast.BuiltInFun.IfThenElse)
                        ),
                        self.i.compile(),
                    ),
                    uplc_ast.Delay(self.t.compile()),
                ),
                uplc_ast.Delay(self.e.compile()),
            )
        )

    def dumps(self) -> str:
        return f"(if {self.i.dumps()} then {self.t.dumps()} else {self.e.dumps()}"
