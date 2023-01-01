import enum
from dataclasses import dataclass
import typing

from . import uplc_ast


class AST:
    def compile(self) -> uplc_ast.AST:
        raise NotImplementedError()

    def dumps(self) -> str:
        raise NotImplementedError()

@dataclass
class Program(AST):
    version: str
    prog: AST

    def compile(self):
        return uplc_ast.Program(self.version, self.prog.compile())

    def dumps(self) -> str:
        # There is no equivalent in "pure" pluto
        return self.prog.dumps()

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
        return f"(\\{' '.join(self.vars)} -> {self.term.dumps()})"


@dataclass
class Apply(AST):
    f: AST
    xs: typing.List[AST]

    def __init__(self, f, *xs) -> None:
        super().__init__()
        self.f = f
        self.xs = xs

    def compile(self):
        f = self.f.compile()
        for x in self.xs:
            f = uplc_ast.Apply(f, x.compile())
        return f

    def dumps(self) -> str:
        return f"({self.f.dumps()} {' '.join(x.dumps() for x in self.xs)})"


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
            uplc_ast.ConstantType.string, f"\"{self.x}\""
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
class Unit(AST):

    def compile(self):
        return uplc_ast.Constant(uplc_ast.ConstantType.unit, "()")

    def dumps(self) -> str:
        return "()"

@dataclass
class BuiltIn(AST):
    builtin: uplc_ast.BuiltInFun

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
        return f"(if {self.i.dumps()} then {self.t.dumps()} else {self.e.dumps()})"

########## Pluto Abstractions that simplify handling complex structures ####################

class Tuple(AST):

    def __new__(cls, *vs: AST) -> "Tuple":
        # idea: just construct a nested if/else comparison
        if not vs:
            return Unit()
        param = Var("__f__")
        return Lambda([param.name], Apply(param, vs))

class TupleAccess(AST):

    def __new__(cls, tuple: AST, index: int, size: int):
        return Apply(Lambda([f"v{i}" for i in range(size)], Var(f"v{index}")), tuple)


class UpdatableMap(AST):

    def __new__(cls) -> "UpdatableMap":
        return Lambda(["x"], Error())

EQUALS_MAP = {
    ByteString: uplc_ast.BuiltInFun.EqualsByteString,
    Integer: uplc_ast.BuiltInFun.EqualsInteger,
}

def extend_map(
    names: typing.List[typing.Any],
    values: typing.List[AST],
    old_statemonad: UpdatableMap,
    keytype = ByteString
) -> UpdatableMap:
    additional_compares = Apply(
        old_statemonad,
        Var("x"),
    )
    for name, value in zip(names, values):
        additional_compares = Ite(
            Apply(
                BuiltIn(EQUALS_MAP[keytype]),
                Var("x"),
                keytype(name),
            ),
            value,
            additional_compares,
        )
    return Lambda(
        ["x"],
        additional_compares,
    )


TOPRIMITIVEVALUE = b"0"
DICT = b"1"

class WrappedValue():

    def __new__(cls, uplc_obj: AST, attributes: UpdatableMap):
        updated_map = extend_map([TOPRIMITIVEVALUE, DICT], [uplc_obj, attributes], attributes)
        return updated_map


def to_primitive_value(wv: WrappedValue):
    return Apply(wv, TOPRIMITIVEVALUE)

def to_dict(wv: WrappedValue) -> UpdatableMap:
    return Apply(wv, DICT)

class AttributeAccess():

    def __new__(cls, wv: WrappedValue, attribute_name: str):
        return Apply(wv, attribute_name.encode())


# self is the simplest source of non-infinitely recursing, complete, integer attributes
INTEGER_ATTRIBUTES_MAP = {
    "__add__": Lambda(
        ["self", "other"],
        WrappedValue(Apply(uplc_ast.BuiltInFun.AddInteger, to_primitive_value(Var("self")), to_primitive_value(Var("other"))), to_dict(Var("self")))
    ),
    "__sub__": Lambda(
        ["self", "other"],
        WrappedValue(Apply(uplc_ast.BuiltInFun.SubtractInteger, to_primitive_value(Var("self")), to_primitive_value(Var("other"))), to_dict(Var("self")))
    ),
    "__eq__": Lambda(
        ["self", "other"],
        WrappedValue(Apply(uplc_ast.BuiltInFun.EqualsInteger, to_primitive_value(Var("self")), to_primitive_value(Var("other"))), to_dict(Var("self")))
    ),
}
INTEGER_ATTRIBUTES = extend_map(
    [k.encode() for k in INTEGER_ATTRIBUTES_MAP.keys()],
    INTEGER_ATTRIBUTES_MAP.values(),
    UpdatableMap(),
)

def from_primitive_int(i: Integer):
    return WrappedValue(i, INTEGER_ATTRIBUTES)