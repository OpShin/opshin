import typing
from dataclasses import dataclass, field
from typing import Callable

import itertools
import ast

from frozendict import frozendict
from frozenlist2 import frozenlist
from ordered_set import OrderedSet

import uplc.ast as uplc
import pluthon as plt

from .util import patternize, OVar, OLet, OLambda, OPSHIN_LOGGER, SafeOLambda, distinct

if typing.TYPE_CHECKING:
    from .typed_ast import TypedAST


class TypeInferenceError(AssertionError):
    pass


class Type:
    def __new__(meta, *args, **kwargs):
        klass = super().__new__(meta)

        for key in ["constr", "attribute", "cmp", "stringify", "copy_only_attributes"]:
            value = getattr(klass, key)
            wrapped = patternize(value)
            object.__setattr__(klass, key, wrapped)

        return klass

    def __ge__(self, other: "Type"):
        """
        Returns whether other can be substituted for this type.
        In other words this returns whether the interface of this type is a subset of the interface of other.
        Note that this is usually <= and not >=, but this needs to be fixed later.
        Produces a partial order on types.
        The top element is the most generic type and can not substitute for anything.
        The bottom element is the most specific type and can be substituted for anything.
        """
        raise NotImplementedError("Comparison between raw types impossible")

    def constr_type(self) -> "InstanceType":
        """The type of the constructor for this class"""
        raise TypeInferenceError(
            f"Object of type {self.__class__} does not have a constructor"
        )

    def constr(self) -> plt.AST:
        """The constructor for this class"""
        raise NotImplementedError(
            f"Constructor of {self.python_type()} not implemented"
        )

    def attribute_type(self, attr) -> "Type":
        """The types of the named attributes of this class"""
        raise TypeInferenceError(
            f"Object of type {self.python_type()} does not have attribute '{attr}'"
        )

    def attribute(self, attr) -> plt.AST:
        """The attributes of this class. Needs to be a lambda that expects as first argument the object itself"""
        raise NotImplementedError(f"Attribute {attr} not implemented for type {self}")

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        raise NotImplementedError(
            f"Comparison {type(op).__name__} for {self.python_type()} and {o.python_type()} is not implemented. This is likely intended because it would always evaluate to False."
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        """
        Returns a stringified version of the object

        The recursive parameter informs the method whether it was invoked recursively from another invokation
        """
        raise NotImplementedError(f"{self.python_type()} can not be stringified")

    def copy_only_attributes(self) -> plt.AST:
        """
        Pluthon function that returns a copy of only the attributes of the object
        This can only be called for UnionType and RecordType, as such the input data is always in PlutusData format and the output should be as well.
        """
        raise NotImplementedError(f"{self.python_type()} can not be copied")

    def binop_type(self, binop: ast.operator, other: "Type") -> "Type":
        """
        Type of a binary operation between self and other.
        """
        return FunctionType(
            [InstanceType(self), InstanceType(other)],
            InstanceType(self._binop_return_type(binop, other)),
        )

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        """
        Return the type of a binary operation between self and other
        """
        raise NotImplementedError(
            f"{self.python_type()} does not implement {binop.__class__.__name__} with {other.python_type()}"
        )

    def binop(self, binop: ast.operator, other: "TypedAST") -> plt.AST:
        """
        Implements a binary operation between self and other
        """
        return OLambda(
            ["self", "other"],
            self._binop_bin_fun(binop, other)(OVar("self"), OVar("other")),
        )

    def _binop_bin_fun(
        self, binop: ast.operator, other: "TypedAST"
    ) -> Callable[[plt.AST, plt.AST], plt.AST]:
        """
        Returns a binary function that implements the binary operation between self and other.
        """
        raise NotImplementedError(
            f"{self.python_type()} can not be used with operation {binop.__class__.__name__} with {other.type.python_type()}"
        )

    def unop_type(self, unop: ast.unaryop) -> "Type":
        """
        Type of a unary operation on self.
        """
        return FunctionType(
            [InstanceType(self)],
            InstanceType(self._unop_return_type(unop)),
        )

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        """
        Return the type of a binary operation between self and other
        """
        raise NotImplementedError(
            f"{self.python_type()} does not implement {unop.__class__.__name__}"
        )

    def unop(self, unop: ast.unaryop) -> plt.AST:
        """
        Implements a unary operation on self
        """
        return OLambda(
            ["self"],
            self._unop_fun(unop)(OVar("self")),
        )

    def _unop_fun(self, unop: ast.unaryop) -> Callable[[plt.AST], plt.AST]:
        """
        Returns a unary function that implements the unary operation on self.
        """
        raise NotImplementedError(
            f"{self.python_type()} can not be used with operation {unop.__class__.__name__}"
        )

    def pluthon_type(self, skip_constructor: bool = False) -> str:
        """
        Returns a representation of the type in pluthon.
        """
        raise NotImplementedError(
            f"Type {self.python_type()} does not have a pluthon representation"
        )

    def python_type(self):
        """
        Returns a representation of the type in python.
        """
        raise NotImplementedError(
            f"Type {type(self).__name__} does not have a python type representation"
        )


@dataclass(frozen=True, unsafe_hash=True)
class Record:
    name: str
    orig_name: str
    constructor: int
    fields: typing.Union[typing.List[typing.Tuple[str, Type]], frozenlist]

    def __post_init__(self):
        object.__setattr__(self, "fields", frozenlist(self.fields))

    def __ge__(self, other):
        assert isinstance(other, Record), "Can only compare Records to Records"
        return (
            self.constructor == other.constructor
            and len(self.fields) == len(other.fields)
            and all(a >= b for a, b in zip(self.fields, other.fields))
        )


@dataclass(frozen=True, unsafe_hash=True)
class ClassType(Type):
    def __ge__(self, other):
        """
        Returns whether other can be substituted for this type.
        In other words this returns whether the interface of this type is a subset of the interface of other.
        Note that this is usually <= and not >=, but this needs to be fixed later.
        Produces a partial order on types.
        The top element is the most generic type and can not substitute for anything.
        The bottom element is the most specific type and can be substituted for anything.
        """
        raise NotImplementedError("Comparison between raw classtypes impossible")


@dataclass(frozen=True, unsafe_hash=True)
class AnyType(ClassType):
    """The top element in the partial order on types (excluding FunctionTypes, which do not compare to anything)"""

    def pluthon_type(self, skip_constructor: bool = False) -> str:
        return "any"

    def python_type(self):
        return "Any"

    def attribute_type(self, attr: str) -> Type:
        """The types of the named attributes of this class"""
        return super().attribute_type(attr)

    def attribute(self, attr: str) -> plt.AST:
        """The attributes of this class. Need to be a lambda that expects as first argument the object itself"""
        return super().attribute(attr)

    def __ge__(self, other):
        return (
            isinstance(other, ClassType)
            and not isinstance(other, FunctionType)
            and not isinstance(other, PolymorphicFunctionType)
        )

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        # this will reject comparisons that will always be false - most likely due to faults during programming
        if (
            (isinstance(o, RecordType))
            or isinstance(o, UnionType)
            or isinstance(o, AnyType)
        ):
            # Note that comparison with Record and UnionType is actually fine because both are Data
            if isinstance(op, ast.Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsData)
            if isinstance(op, ast.NotEq):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                            OVar("x"),
                            OVar("y"),
                        )
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and (o.typ.typ >= self or self >= o.typ.typ)
        ):
            if isinstance(op, ast.In):
                return OLambda(
                    ["x", "y"],
                    plt.AnyList(
                        OVar("y"),
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                            OVar("x"),
                        ),
                    ),
                )
            if isinstance(op, ast.NotIn):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.AnyList(
                            OVar("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                                OVar("x"),
                            ),
                        ),
                    ),
                )
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        OPSHIN_LOGGER.warning(
            "Serializing AnyType will result in RawPlutusData (CBOR representation) to be printed without additional type information. Annotate types where possible to avoid this warning."
        )
        return OLambda(
            ["self"],
            OLet(
                [
                    (
                        "joinMapList",
                        OLambda(
                            ["m", "l", "start", "end"],
                            OLet(
                                [
                                    (
                                        "g",
                                        plt.RecFun(
                                            OLambda(
                                                ["f", "l"],
                                                plt.AppendString(
                                                    plt.Apply(
                                                        OVar("m"),
                                                        plt.HeadList(OVar("l")),
                                                    ),
                                                    OLet(
                                                        [
                                                            (
                                                                "t",
                                                                plt.TailList(OVar("l")),
                                                            )
                                                        ],
                                                        plt.IteNullList(
                                                            OVar("t"),
                                                            OVar("end"),
                                                            plt.AppendString(
                                                                plt.Text(", "),
                                                                plt.Apply(
                                                                    OVar("f"),
                                                                    OVar("f"),
                                                                    OVar("t"),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            )
                                        ),
                                    )
                                ],
                                plt.AppendString(
                                    OVar("start"),
                                    plt.IteNullList(
                                        OVar("l"),
                                        OVar("end"),
                                        plt.Apply(
                                            OVar("g"),
                                            OVar("l"),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stringifyPlutusData",
                        plt.RecFun(
                            OLambda(
                                ["f", "d"],
                                plt.DelayedChooseData(
                                    OVar("d"),
                                    OLet(
                                        [
                                            (
                                                "constructor",
                                                plt.FstPair(
                                                    plt.UnConstrData(OVar("d"))
                                                ),
                                            )
                                        ],
                                        plt.Ite(
                                            plt.LessThanInteger(
                                                OVar("constructor"),
                                                plt.Integer(128),
                                            ),
                                            plt.ConcatString(
                                                plt.Text("CBORTag("),
                                                plt.Apply(
                                                    OVar("f"),
                                                    OVar("f"),
                                                    plt.IData(
                                                        plt.AddInteger(
                                                            OVar("constructor"),
                                                            plt.Ite(
                                                                plt.LessThanInteger(
                                                                    OVar("constructor"),
                                                                    plt.Integer(7),
                                                                ),
                                                                plt.Integer(121),
                                                                plt.Integer(1280 - 7),
                                                            ),
                                                        )
                                                    ),
                                                ),
                                                plt.Text(", "),
                                                plt.Apply(
                                                    OVar("f"),
                                                    OVar("f"),
                                                    plt.ListData(
                                                        plt.SndPair(
                                                            plt.UnConstrData(OVar("d"))
                                                        )
                                                    ),
                                                ),
                                                plt.Text(")"),
                                            ),
                                            plt.ConcatString(
                                                plt.Text("CBORTag(102, "),
                                                plt.Apply(
                                                    OVar("f"),
                                                    OVar("f"),
                                                    plt.ListData(
                                                        plt.MkCons(
                                                            plt.IData(
                                                                OVar("constructor")
                                                            ),
                                                            plt.MkCons(
                                                                plt.ListData(
                                                                    plt.SndPair(
                                                                        plt.UnConstrData(
                                                                            OVar("d")
                                                                        )
                                                                    )
                                                                ),
                                                                plt.EmptyDataList(),
                                                            ),
                                                        )
                                                    ),
                                                ),
                                                plt.Text(")"),
                                            ),
                                        ),
                                    ),
                                    plt.Apply(
                                        OVar("joinMapList"),
                                        OLambda(
                                            ["x"],
                                            plt.ConcatString(
                                                plt.Apply(
                                                    OVar("f"),
                                                    OVar("f"),
                                                    plt.FstPair(OVar("x")),
                                                ),
                                                plt.Text(": "),
                                                plt.Apply(
                                                    OVar("f"),
                                                    OVar("f"),
                                                    plt.SndPair(OVar("x")),
                                                ),
                                            ),
                                        ),
                                        plt.UnMapData(OVar("d")),
                                        plt.Text("{"),
                                        plt.Text("}"),
                                    ),
                                    plt.Apply(
                                        OVar("joinMapList"),
                                        OLambda(
                                            ["x"],
                                            plt.Apply(
                                                OVar("f"),
                                                OVar("f"),
                                                OVar("x"),
                                            ),
                                        ),
                                        plt.UnListData(OVar("d")),
                                        plt.Text("["),
                                        plt.Text("]"),
                                    ),
                                    plt.Apply(
                                        IntegerInstanceType.stringify(recursive=True),
                                        plt.UnIData(OVar("d")),
                                    ),
                                    plt.Apply(
                                        ByteStringInstanceType.stringify(
                                            recursive=True
                                        ),
                                        plt.UnBData(OVar("d")),
                                    ),
                                ),
                            )
                        ),
                    ),
                ],
                plt.ConcatString(
                    plt.Text("RawPlutusData(data="),
                    plt.Apply(OVar("stringifyPlutusData"), OVar("self")),
                    plt.Text(")"),
                ),
            ),
        )

    def copy_only_attributes(self) -> plt.AST:
        """Any is always valid, just returns"""
        return OLambda(["self"], OVar("self"))


@dataclass(frozen=True, unsafe_hash=True)
class AtomicType(ClassType):
    def __ge__(self, other):
        # Can only substitute for its own type (also subtypes)
        return isinstance(other, self.__class__)


@dataclass(frozen=True, unsafe_hash=True)
class RecordType(ClassType):
    record: Record

    def pluthon_type(self, skip_constructor: bool = False) -> str:
        return (
            "cons["
            + self.record.orig_name
            + "]("
            + (str(self.record.constructor) if not skip_constructor else "_")
            + ";"
            + ",".join(
                name + ":" + type.pluthon_type() for name, type in self.record.fields
            )
            + ")"
        )

    def python_type(self):
        return (
            f"class {self.record.orig_name}(CONSTR_ID={self.record.constructor}, "
            + ", ".join(
                f"{name}: {type.python_type()}" for name, type in self.record.fields
            )
            + ")"
        )

    def constr_type(self) -> "InstanceType":
        return InstanceType(
            FunctionType(
                frozenlist([f[1] for f in self.record.fields]), InstanceType(self)
            )
        )

    def constr(self) -> plt.AST:
        # wrap all constructor values to PlutusData
        build_constr_params = plt.EmptyDataList()
        for n, t in reversed(self.record.fields):
            build_constr_params = plt.MkCons(
                transform_output_map(t)(plt.Force(OVar(n))), build_constr_params
            )
        # then build a constr type with this PlutusData
        return SafeOLambda(
            [n for n, _ in self.record.fields],
            plt.ConstrData(plt.Integer(self.record.constructor), build_constr_params),
        )

    def attribute_type(self, attr: str) -> Type:
        """The types of the named attributes of this class"""
        if attr == "CONSTR_ID":
            return IntegerInstanceType
        for n, t in self.record.fields:
            if n == attr:
                return t
        if attr == "to_cbor":
            return InstanceType(FunctionType(frozenlist([]), ByteStringInstanceType))
        super().attribute_type(attr)

    def attribute(self, attr: str) -> plt.AST:
        """The attributes of this class. Need to be a lambda that expects as first argument the object itself"""
        if attr == "CONSTR_ID":
            # access to constructor
            return OLambda(
                ["self"],
                plt.Constructor(OVar("self")),
            )
        if attr in (n for n, t in self.record.fields):
            attr_typ = self.attribute_type(attr)
            pos = next(i for i, (n, _) in enumerate(self.record.fields) if n == attr)
            # access to normal fields
            return OLambda(
                ["self"],
                transform_ext_params_map(attr_typ)(
                    plt.ConstantNthFieldFast(
                        OVar("self"),
                        pos,
                    ),
                ),
            )
        if attr == "to_cbor":
            return OLambda(
                ["self", "_"],
                plt.SerialiseData(
                    OVar("self"),
                ),
            )
        raise NotImplementedError(f"Attribute {attr} not implemented for type {self}")

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        # this will reject comparisons that will always be false - most likely due to faults during programming
        if (
            (
                isinstance(o, RecordType)
                and (self.record >= o.record or o.record >= self.record)
            )
            or (
                isinstance(o, UnionType) and any(self >= o or self >= o for o in o.typs)
            )
            or isinstance(o, AnyType)
        ):
            # Note that comparison with AnyType is actually fine because both are Data
            if isinstance(op, ast.Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsData)
            if isinstance(op, ast.NotEq):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                            OVar("x"),
                            OVar("y"),
                        )
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and (o.typ.typ >= self or self >= o.typ.typ)
        ):
            if isinstance(op, ast.In):
                return OLambda(
                    ["x", "y"],
                    plt.AnyList(
                        OVar("y"),
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                            OVar("x"),
                        ),
                    ),
                )
            if isinstance(op, ast.NotIn):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.AnyList(
                            OVar("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                                OVar("x"),
                            ),
                        ),
                    ),
                )
        return super().cmp(op, o)

    def __ge__(self, other):
        # Can only substitute for its own type, records need to be equal
        # if someone wants to be funny, they can implement <= to be true if all fields match up to some point
        return isinstance(other, self.__class__) and self.record >= other.record

    def stringify(self, recursive: bool = False) -> plt.AST:
        """Returns a stringified version of the object"""
        map_fields = plt.Text(")")
        if self.record.fields:
            # TODO access to fields is a bit inefficient but this is debugging stuff only anyways
            pos = len(self.record.fields) - 1
            for field_name, field_type in reversed(self.record.fields[1:]):
                map_fields = plt.ConcatString(
                    plt.Text(f", {field_name}="),
                    plt.Apply(
                        field_type.stringify(recursive=True),
                        transform_ext_params_map(field_type)(
                            plt.ConstantNthFieldFast(OVar("self"), pos)
                        ),
                    ),
                    map_fields,
                )
                pos -= 1
            map_fields = plt.ConcatString(
                plt.Text(f"{self.record.fields[0][0]}="),
                plt.Apply(
                    self.record.fields[0][1].stringify(recursive=True),
                    transform_ext_params_map(self.record.fields[0][1])(
                        plt.ConstantNthFieldFast(OVar("self"), pos)
                    ),
                ),
                map_fields,
            )
        return OLambda(
            ["self"],
            plt.AppendString(plt.Text(f"{self.record.orig_name}("), map_fields),
        )

    def copy_only_attributes(self) -> plt.AST:
        copied_attributes = plt.EmptyDataList()
        for attr_name, attr_type in reversed(self.record.fields):
            copied_attributes = OLet(
                [
                    ("f", plt.HeadList(OVar("fs"))),
                    ("fs", plt.TailList(OVar("fs"))),
                ],
                plt.MkCons(
                    plt.Apply(
                        attr_type.copy_only_attributes(),
                        OVar("f"),
                    ),
                    copied_attributes,
                ),
            )
        copied_attributes = OLet(
            [("fs", plt.Fields(OVar("self")))],
            copied_attributes,
        )
        return OLambda(
            ["self"],
            plt.DelayedChooseData(
                OVar("self"),
                plt.ConstrData(
                    plt.Integer(self.record.constructor),
                    copied_attributes,
                ),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusMap, but got PlutusDict"
                ),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusMap, but got PlutusList"
                ),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusMap, but got PlutusInteger"
                ),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusMap, but got PlutusByteString"
                ),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class UnionType(ClassType):
    typs: typing.List[Type]

    def __post_init__(self):
        object.__setattr__(self, "typs", frozenlist(self.typs))

    def pluthon_type(self, skip_constructor: bool = False) -> str:
        return "union<" + ",".join(t.pluthon_type() for t in self.typs) + ">"

    def python_type(self):
        return "Union[" + ", ".join(t.python_type() for t in self.typs) + "]"

    def attribute_type(self, attr) -> "Type":
        record_only = all(isinstance(x, RecordType) for x in self.typs)
        if attr == "CONSTR_ID" and record_only:
            # constructor is only guaranteed to be present if all types are record types
            return IntegerInstanceType
        # need to have a common field with the same name
        if record_only and all(
            attr in (n for n, t in x.record.fields) for x in self.typs
        ):
            attr_types = OrderedSet(
                t for x in self.typs for n, t in x.record.fields if n == attr
            )
            for at in attr_types:
                # return the maximum element if there is one
                if all(at >= at2 for at2 in attr_types):
                    return at
            # return the union type of all possible instantiations if all possible values are record types
            if all(
                isinstance(at, InstanceType) and isinstance(at.typ, RecordType)
                for at in attr_types
            ) and distinct([at.typ.record.constructor for at in attr_types]):
                return InstanceType(
                    UnionType(frozenlist([at.typ for at in attr_types]))
                )
            # return Anytype
            return InstanceType(AnyType())
        if attr == "to_cbor":
            return InstanceType(FunctionType(frozenlist([]), ByteStringInstanceType))
        raise TypeInferenceError(
            f"Can not access attribute {attr} of Union type. Cast to desired type with an 'if isinstance(_, _):' branch."
        )

    def attribute(self, attr: str) -> plt.AST:
        if attr == "CONSTR_ID":
            # access to constructor
            return OLambda(
                ["self"],
                plt.Constructor(OVar("self")),
            )
        # iterate through all names/types of the unioned records by position
        if any(attr in (n for n, t in r.record.fields) for r in self.typs):
            attr_typ = self.attribute_type(attr)
            pos_constrs = [
                (i, x.record.constructor)
                for x in self.typs
                for i, (n, t) in enumerate(x.record.fields)
                if n == attr
            ]
            pos_constrs = sorted(pos_constrs, key=lambda x: x[0])
            pos_constrs = [
                (pos, [c[1] for c in constrs])
                for (pos, constrs) in itertools.groupby(pos_constrs, key=lambda x: x[0])
            ]
            # largest group last so we save the comparisons for that
            pos_constrs = sorted(pos_constrs, key=lambda x: len(x[1]))
            # access to normal fields
            if not pos_constrs:
                pos_decisor = plt.TraceError("Invalid constructor")
            else:
                pos_decisor = plt.ConstantNthFieldFast(OVar("self"), pos_constrs[-1][0])
                pos_constrs = pos_constrs[:-1]
            # constr is not needed when there is only one position for all constructors
            if not pos_constrs:
                return OLambda(
                    ["self"],
                    transform_ext_params_map(attr_typ)(
                        pos_decisor,
                    ),
                )
            for pos, constrs in pos_constrs:
                assert constrs, "Found empty constructors for a position"
                constr_check = plt.EqualsInteger(
                    OVar("constr"), plt.Integer(constrs[0])
                )
                for constr in constrs[1:]:
                    constr_check = plt.Or(
                        plt.EqualsInteger(OVar("constr"), plt.Integer(constr)),
                        constr_check,
                    )
                pos_decisor = plt.Ite(
                    constr_check,
                    plt.ConstantNthFieldFast(OVar("self"), pos),
                    pos_decisor,
                )
            return OLambda(
                ["self"],
                transform_ext_params_map(attr_typ)(
                    OLet(
                        [("constr", plt.Constructor(OVar("self")))],
                        pos_decisor,
                    ),
                ),
            )
        if attr == "to_cbor":
            return OLambda(
                ["self", "_"],
                plt.SerialiseData(
                    OVar("self"),
                ),
            )
        raise NotImplementedError(f"Attribute {attr} not implemented for type {self}")

    def __ge__(self, other):
        if isinstance(other, UnionType):
            return all(self >= ot for ot in other.typs)
        return any(t >= other for t in self.typs)

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        # this will reject comparisons that will always be false - most likely due to faults during programming
        # note we require that there is an overlapt between the possible types for unions
        if (isinstance(o, RecordType) and any(t >= o or o >= t for t in self.typs)) or (
            isinstance(o, UnionType)
            and any(t >= ot or t >= ot for t in self.typs for ot in o.typs)
        ):
            if isinstance(op, ast.Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsData)
            if isinstance(op, ast.NotEq):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                            OVar("x"),
                            OVar("y"),
                        )
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and any(o.typ.typ >= t or t >= o.typ.typ for t in self.typs)
        ):
            if isinstance(op, ast.In):
                return OLambda(
                    ["x", "y"],
                    plt.AnyList(
                        OVar("y"),
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                            OVar("x"),
                        ),
                    ),
                )
            if isinstance(op, ast.NotIn):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.AnyList(
                            OVar("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                                OVar("x"),
                            ),
                        ),
                    ),
                )
        raise NotImplementedError(
            f"Can not compare {o.python_type()} and {self.python_type()} with operation {op.__class__.__name__}. Note that comparisons that always return false are also rejected."
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        decide_string_func = plt.TraceError("Invalid constructor id in Union")
        contains_non_record = False
        for t in self.typs:
            if not isinstance(t, RecordType):
                contains_non_record = True
                continue
            decide_string_func = plt.Ite(
                plt.EqualsInteger(OVar("constr"), plt.Integer(t.record.constructor)),
                t.stringify(recursive=True),
                decide_string_func,
            )
        decide_string_func = OLet(
            [("constr", plt.Constructor(OVar("self")))],
            plt.Apply(decide_string_func, OVar("self")),
        )
        if contains_non_record:
            decide_string_func = plt.DelayedChooseData(
                OVar("self"),
                decide_string_func,
                plt.Apply(
                    DictType(
                        InstanceType(AnyType()), InstanceType(AnyType())
                    ).stringify(recursive=True),
                    plt.UnMapData(OVar("self")),
                ),
                plt.Apply(
                    ListType(InstanceType(AnyType())).stringify(recursive=True),
                    plt.UnListData(OVar("self")),
                ),
                plt.Apply(
                    IntegerType().stringify(recursive=True), plt.UnIData(OVar("self"))
                ),
                plt.Apply(
                    ByteStringType().stringify(recursive=True),
                    plt.UnBData(OVar("self")),
                ),
            )
        return OLambda(
            ["self"],
            decide_string_func,
        )

    def copy_only_attributes(self) -> plt.AST:
        copied_attributes = plt.TraceError(
            f"Invalid CONSTR_ID (no matching type in Union)"
        )
        for typ in self.typs:
            if not isinstance(typ, RecordType):
                continue
            copied_attributes = plt.Ite(
                plt.EqualsInteger(OVar("constr"), plt.Integer(typ.record.constructor)),
                plt.Apply(typ.copy_only_attributes(), OVar("self")),
                copied_attributes,
            )
        record_copier = OLambda(
            ["self"],
            OLet(
                [("constr", plt.Constructor(OVar("self")))],
                copied_attributes,
            ),
        )

        def lambda_false(x: str):
            return OLambda(
                ["_"],
                plt.TraceError("Invalid datatype not in Union, got " + x),
            )

        return OLambda(
            ["self"],
            plt.Apply(
                plt.DelayedChooseData(
                    OVar("self"),
                    record_copier,
                    (
                        DictType(AnyType(), AnyType()).copy_only_attributes()
                        if any(isinstance(x, DictType) for x in self.typs)
                        else lambda_false("dict")
                    ),
                    (
                        ListType(AnyType()).copy_only_attributes()
                        if any(isinstance(x, ListType) for x in self.typs)
                        else lambda_false("list")
                    ),
                    (
                        IntegerType().copy_only_attributes()
                        if IntegerType() in self.typs
                        else lambda_false("int")
                    ),
                    (
                        ByteStringType().copy_only_attributes()
                        if ByteStringType() in self.typs
                        else lambda_false("bytes")
                    ),
                ),
                OVar("self"),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class TupleType(ClassType):
    typs: typing.List[Type]

    def __ge__(self, other):
        return (
            isinstance(other, TupleType)
            and len(self.typs) <= len(other.typs)
            and all(t >= ot for t, ot in zip(self.typs, other.typs))
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        if not self.typs:
            return OLambda(
                ["self"],
                plt.Text("()"),
            )
        elif len(self.typs) == 1:
            tuple_content = plt.ConcatString(
                plt.Apply(
                    self.typs[0].stringify(recursive=True),
                    plt.FunctionalTupleAccess(OVar("self"), 0, len(self.typs)),
                ),
                plt.Text(","),
            )
        else:
            tuple_content = plt.ConcatString(
                plt.Apply(
                    self.typs[0].stringify(recursive=True),
                    plt.FunctionalTupleAccess(OVar("self"), 0, len(self.typs)),
                ),
            )
            for i, t in enumerate(self.typs[1:], start=1):
                tuple_content = plt.ConcatString(
                    tuple_content,
                    plt.Text(", "),
                    plt.Apply(
                        t.stringify(recursive=True),
                        plt.FunctionalTupleAccess(OVar("self"), i, len(self.typs)),
                    ),
                )
        return OLambda(
            ["self"],
            plt.ConcatString(plt.Text("("), tuple_content, plt.Text(")")),
        )

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        if isinstance(binop, ast.Add):
            if isinstance(other, TupleType):
                return TupleType(self.typs + other.typs)
        return super()._binop_return_type(binop, other)

    def python_type(self) -> str:
        return f"Tuple[{', '.join(t.python_type() for t in self.typs)}]"


@dataclass(frozen=True, unsafe_hash=True)
class PairType(ClassType):
    """An internal type representing built-in PlutusData pairs"""

    l_typ: Type
    r_typ: Type

    def __ge__(self, other):
        return isinstance(other, PairType) and all(
            t >= ot
            for t, ot in zip((self.l_typ, self.r_typ), (other.l_typ, other.r_typ))
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        tuple_content = plt.ConcatString(
            plt.Apply(
                self.l_typ.stringify(recursive=True),
                transform_ext_params_map(self.l_typ)(plt.FstPair(OVar("self"))),
            ),
            plt.Text(", "),
            plt.Apply(
                self.r_typ.stringify(recursive=True),
                transform_ext_params_map(self.r_typ)(plt.SndPair(OVar("self"))),
            ),
        )
        return OLambda(
            ["self"],
            plt.ConcatString(plt.Text("("), tuple_content, plt.Text(")")),
        )

    def python_type(self):
        return f"Tuple[{self.l_typ.python_type()}, {self.r_typ.python_type()}]"


@dataclass(frozen=True, unsafe_hash=True)
class ListType(ClassType):
    typ: Type

    def __ge__(self, other):
        return isinstance(other, ListType) and self.typ >= other.typ

    def pluthon_type(self, skip_constructor: bool = False) -> str:
        return "list<" + self.typ.pluthon_type() + ">"

    def python_type(self):
        return f"List[{self.typ.python_type()}]"

    def attribute_type(self, attr) -> "Type":
        if attr == "index":
            return InstanceType(
                FunctionType(frozenlist([self.typ]), IntegerInstanceType)
            )
        super().attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        if attr == "index":
            return OLambda(
                ["self", "x"],
                OLet(
                    [("x", plt.Force(OVar("x")))],
                    plt.Apply(
                        plt.RecFun(
                            OLambda(
                                ["index", "xs", "a"],
                                plt.IteNullList(
                                    OVar("xs"),
                                    plt.TraceError(
                                        "ValueError: Did not find element in list"
                                    ),
                                    plt.Ite(
                                        # the paramter x must have the same type as the list elements
                                        plt.Apply(
                                            self.typ.cmp(ast.Eq(), self.typ),
                                            OVar("x"),
                                            plt.HeadList(OVar("xs")),
                                        ),
                                        OVar("a"),
                                        plt.Apply(
                                            OVar("index"),
                                            OVar("index"),
                                            plt.TailList(OVar("xs")),
                                            plt.AddInteger(OVar("a"), plt.Integer(1)),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        OVar("self"),
                        plt.Integer(0),
                    ),
                ),
            )
        super().attribute(attr)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return OLambda(
            ["self"],
            OLet(
                [
                    (
                        "g",
                        plt.RecFun(
                            OLambda(
                                ["f", "l"],
                                plt.AppendString(
                                    plt.Apply(
                                        self.typ.stringify(recursive=True),
                                        plt.HeadList(OVar("l")),
                                    ),
                                    OLet(
                                        [("t", plt.TailList(OVar("l")))],
                                        plt.IteNullList(
                                            OVar("t"),
                                            plt.Text("]"),
                                            plt.AppendString(
                                                plt.Text(", "),
                                                plt.Apply(
                                                    OVar("f"),
                                                    OVar("f"),
                                                    OVar("t"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            )
                        ),
                    )
                ],
                plt.AppendString(
                    plt.Text("["),
                    plt.IteNullList(
                        OVar("self"),
                        plt.Text("]"),
                        plt.Apply(
                            OVar("g"),
                            OVar("self"),
                        ),
                    ),
                ),
            ),
        )

    def copy_only_attributes(self) -> plt.AST:
        mapped_attrs = plt.MapList(
            plt.UnListData(OVar("self")),
            OLambda(
                ["v"],
                plt.Apply(
                    self.typ.copy_only_attributes(),
                    OVar("v"),
                ),
            ),
            plt.EmptyDataList(),
        )
        return OLambda(
            ["self"],
            plt.DelayedChooseData(
                OVar("self"),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusList, but got PlutusData"
                ),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusList, but got PlutusMap"
                ),
                plt.ListData(mapped_attrs),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusList, but got PlutusInteger"
                ),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusList, but got PlutusByteString"
                ),
            ),
        )

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        if isinstance(o, ListType) and (self.typ >= o.typ or o.typ >= self.typ):
            if isinstance(op, ast.Eq):
                # Implement list equality comparison
                # This is expensive (linear in the size of the list) as noted in the feature request
                return OLambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.RecFun(
                            OLambda(
                                ["f", "xs", "ys"],
                                plt.IteNullList(
                                    OVar("xs"),
                                    # If first list is empty, check if second is also empty
                                    plt.NullList(OVar("ys")),
                                    plt.IteNullList(
                                        OVar("ys"),
                                        # If second list is empty but first is not, they're not equal
                                        plt.Bool(False),
                                        # Both lists have elements, compare heads and recurse on tails
                                        plt.And(
                                            plt.Apply(
                                                self.typ.cmp(op, o.typ),
                                                plt.HeadList(OVar("xs")),
                                                plt.HeadList(OVar("ys")),
                                            ),
                                            plt.Apply(
                                                OVar("f"),
                                                OVar("f"),
                                                plt.TailList(OVar("xs")),
                                                plt.TailList(OVar("ys")),
                                            ),
                                        ),
                                    ),
                                ),
                            )
                        ),
                        OVar("x"),
                        OVar("y"),
                    ),
                )
            if isinstance(op, ast.NotEq):
                # Implement list inequality comparison as negation of equality
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            self.cmp(ast.Eq(), o),
                            OVar("x"),
                            OVar("y"),
                        )
                    ),
                )
        return super().cmp(op, o)

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        if isinstance(binop, ast.Add):
            if isinstance(other, InstanceType) and isinstance(other.typ, ListType):
                other_typ = other.typ
                assert (
                    self.typ >= other_typ.typ or other_typ.typ >= self.typ
                ), f"Types of lists {self.typ} and {other_typ.typ} are not compatible"
                return ListType(
                    self.typ if self.typ >= other_typ.typ else other_typ.typ
                )
        return super()._binop_return_type(binop, other)

    def _binop_bin_fun(self, binop: ast.operator, other: "TypedAST"):
        if isinstance(binop, ast.Add):
            if isinstance(other.typ, InstanceType) and isinstance(
                other.typ.typ, ListType
            ):
                return plt.AppendList
        return super()._binop_bin_fun(binop, other)

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, ast.Not):
            return BoolType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop) -> Callable[[plt.AST], plt.AST]:
        if isinstance(unop, ast.Not):
            return lambda x: plt.IteNullList(x, plt.Bool(True), plt.Bool(False))
        return super()._unop_fun(unop)


@dataclass(frozen=True, unsafe_hash=True)
class DictType(ClassType):
    key_typ: Type
    value_typ: Type

    def pluthon_type(self, skip_constructor: bool = False) -> str:
        return (
            "map<"
            + self.key_typ.pluthon_type()
            + ","
            + self.value_typ.pluthon_type()
            + ">"
        )

    def python_type(self):
        return f"Dict[{self.key_typ.python_type()}, {self.value_typ.python_type()}]"

    def attribute_type(self, attr) -> "Type":
        if attr == "get":
            return InstanceType(
                FunctionType(frozenlist([self.key_typ, self.value_typ]), self.value_typ)
            )
        if attr == "keys":
            return InstanceType(
                FunctionType(frozenlist([]), InstanceType(ListType(self.key_typ)))
            )
        if attr == "values":
            return InstanceType(
                FunctionType(frozenlist([]), InstanceType(ListType(self.value_typ)))
            )
        if attr == "items":
            return InstanceType(
                FunctionType(
                    frozenlist([]),
                    InstanceType(
                        ListType(InstanceType(PairType(self.key_typ, self.value_typ)))
                    ),
                )
            )
        raise TypeInferenceError(
            f"Type of attribute '{attr}' is unknown for type Dict."
        )

    def attribute(self, attr) -> plt.AST:
        if attr == "get":
            return OLambda(
                ["self", "key", "default"],
                transform_ext_params_map(self.value_typ)(
                    OLet(
                        [
                            (
                                "key_mapped",
                                transform_output_map(self.key_typ)(
                                    plt.Force(OVar("key"))
                                ),
                            )
                        ],
                        plt.SndPair(
                            plt.FindList(
                                OVar("self"),
                                OLambda(
                                    ["x"],
                                    plt.EqualsData(
                                        OVar("key_mapped"),
                                        plt.FstPair(OVar("x")),
                                    ),
                                ),
                                # this is a bit ugly... we wrap - only to later unwrap again
                                plt.MkPairData(
                                    OVar("key_mapped"),
                                    transform_output_map(self.value_typ)(
                                        plt.Force(OVar("default"))
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        if attr == "keys":
            return OLambda(
                ["self", "_"],
                plt.MapList(
                    OVar("self"),
                    OLambda(
                        ["x"],
                        transform_ext_params_map(self.key_typ)(plt.FstPair(OVar("x"))),
                    ),
                    empty_list(self.key_typ),
                ),
            )
        if attr == "values":
            return OLambda(
                ["self", "_"],
                plt.MapList(
                    OVar("self"),
                    OLambda(
                        ["x"],
                        transform_ext_params_map(self.value_typ)(
                            plt.SndPair(OVar("x"))
                        ),
                    ),
                    empty_list(self.value_typ),
                ),
            )
        if attr == "items":
            return OLambda(
                ["self", "_"],
                OVar("self"),
            )
        raise NotImplementedError(f"Attribute '{attr}' of Dict is unknown.")

    def __ge__(self, other):
        return (
            isinstance(other, DictType)
            and self.key_typ >= other.key_typ
            and self.value_typ >= other.value_typ
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        return OLambda(
            ["self"],
            OLet(
                [
                    (
                        "g",
                        plt.RecFun(
                            OLambda(
                                ["f", "l"],
                                OLet(
                                    [
                                        ("h", plt.HeadList(OVar("l"))),
                                        ("t", plt.TailList(OVar("l"))),
                                    ],
                                    plt.ConcatString(
                                        plt.Apply(
                                            self.key_typ.stringify(recursive=True),
                                            transform_ext_params_map(self.key_typ)(
                                                plt.FstPair(OVar("h"))
                                            ),
                                        ),
                                        plt.Text(": "),
                                        plt.Apply(
                                            self.value_typ.stringify(recursive=True),
                                            transform_ext_params_map(self.value_typ)(
                                                plt.SndPair(OVar("h"))
                                            ),
                                        ),
                                        plt.IteNullList(
                                            OVar("t"),
                                            plt.Text("}"),
                                            plt.AppendString(
                                                plt.Text(", "),
                                                plt.Apply(
                                                    OVar("f"),
                                                    OVar("f"),
                                                    OVar("t"),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            )
                        ),
                    )
                ],
                plt.AppendString(
                    plt.Text("{"),
                    plt.IteNullList(
                        OVar("self"),
                        plt.Text("}"),
                        plt.Apply(
                            OVar("g"),
                            OVar("self"),
                        ),
                    ),
                ),
            ),
        )

    def copy_only_attributes(self) -> plt.AST:
        def CustomMapFilterList(
            l: plt.AST,
            filter_op: plt.AST,
            map_op: plt.AST,
            empty_list=plt.EmptyDataList(),
        ):
            from pluthon import (
                Apply,
                Lambda as PLambda,
                RecFun,
                IteNullList,
                Var as PVar,
                HeadList,
                Ite,
                TailList,
                PrependList,
                Let as PLet,
            )

            """
            Apply a filter and a map function on each element in a list (throws out all that evaluate to false)
            Performs only a single pass and is hence much more efficient than filter + map
            """
            return Apply(
                PLambda(
                    ["filter", "map"],
                    RecFun(
                        PLambda(
                            ["filtermap", "xs"],
                            IteNullList(
                                PVar("xs"),
                                empty_list,
                                PLet(
                                    [
                                        ("head", HeadList(PVar("xs"))),
                                        ("tail", TailList(PVar("xs"))),
                                    ],
                                    Ite(
                                        Apply(
                                            PVar("filter"), PVar("head"), PVar("tail")
                                        ),
                                        PrependList(
                                            Apply(PVar("map"), PVar("head")),
                                            Apply(
                                                PVar("filtermap"),
                                                PVar("filtermap"),
                                                PVar("tail"),
                                            ),
                                        ),
                                        Apply(
                                            PVar("filtermap"),
                                            PVar("filtermap"),
                                            PVar("tail"),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                filter_op,
                map_op,
                l,
            )

        mapped_attrs = CustomMapFilterList(
            plt.UnMapData(OVar("self")),
            OLambda(
                ["h", "t"],
                OLet(
                    [
                        ("hfst", plt.FstPair(OVar("h"))),
                    ],
                    plt.Not(
                        plt.AnyList(
                            OVar("t"),
                            OLambda(
                                ["e"],
                                plt.EqualsData(OVar("hfst"), plt.FstPair(OVar("e"))),
                            ),
                        )
                    ),
                ),
            ),
            OLambda(
                ["v"],
                plt.MkPairData(
                    plt.Apply(
                        self.key_typ.copy_only_attributes(), plt.FstPair(OVar("v"))
                    ),
                    plt.Apply(
                        self.value_typ.copy_only_attributes(), plt.SndPair(OVar("v"))
                    ),
                ),
            ),
            plt.EmptyDataPairList(),
        )
        return OLambda(
            ["self"],
            plt.DelayedChooseData(
                OVar("self"),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusMap, but got PlutusData"
                ),
                plt.MapData(mapped_attrs),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusMap, but got PlutusList"
                ),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusMap, but got PlutusInteger"
                ),
                plt.TraceError(
                    "IntegrityError: Expected a PlutusMap, but got PlutusByteString"
                ),
            ),
        )

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, ast.Not):
            return BoolType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop) -> Callable[[plt.AST], plt.AST]:
        if isinstance(unop, ast.Not):
            return lambda x: plt.IteNullList(x, plt.Bool(True), plt.Bool(False))
        return super()._unop_fun(unop)


@dataclass(frozen=True, unsafe_hash=True)
class FunctionType(ClassType):
    argtyps: typing.List[Type]
    rettyp: Type
    # A map from external variable names to their types when the function is defined
    bound_vars: typing.Dict[str, Type] = field(default_factory=frozendict)
    # Whether and under which name the function binds itself
    # The type of this variable is "self"
    bind_self: typing.Optional[str] = None

    def __post_init__(self):
        object.__setattr__(self, "argtyps", frozenlist(self.argtyps))
        object.__setattr__(self, "bound_vars", frozendict(self.bound_vars))

    def __ge__(self, other):
        return (
            isinstance(other, FunctionType)
            and len(self.argtyps) == len(other.argtyps)
            and all(a >= oa for a, oa in zip(self.argtyps, other.argtyps))
            and self.bound_vars.keys() == other.bound_vars.keys()
            and all(sbv >= other.bound_vars[k] for k, sbv in self.bound_vars.items())
            and self.bind_self == other.bind_self
            and other.rettyp >= self.rettyp
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        return OLambda(["x"], plt.Text("<function>"))

    def python_type(self):
        arg_types = ", ".join(t.python_type() for t in self.argtyps)
        return f"Callable[[{arg_types}], {self.rettyp.python_type()}]"


@dataclass(frozen=True, unsafe_hash=True)
class InstanceType(Type):
    typ: ClassType

    def pluthon_type(self, skip_constructor: bool = False) -> str:
        return self.typ.pluthon_type(skip_constructor=skip_constructor)

    def constr_type(self) -> FunctionType:
        raise TypeInferenceError(f"Can not construct an instance {self}")

    def constr(self) -> plt.AST:
        raise NotImplementedError(f"Can not construct an instance {self}")

    def attribute_type(self, attr) -> Type:
        return self.typ.attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        return self.typ.attribute(attr)

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        if isinstance(o, InstanceType):
            return self.typ.cmp(op, o.typ)
        return super().cmp(op, o)

    def __ge__(self, other):
        return isinstance(other, InstanceType) and self.typ >= other.typ

    def stringify(self, recursive: bool = False) -> plt.AST:
        return self.typ.stringify(recursive=recursive)

    def copy_only_attributes(self) -> plt.AST:
        return self.typ.copy_only_attributes()

    def binop_type(self, binop: ast.operator, other: "Type") -> "Type":
        return self.typ.binop_type(binop, other)

    def binop(self, binop: ast.operator, other: "TypedAST") -> plt.AST:
        return self.typ.binop(binop, other)

    def unop_type(self, unop: ast.unaryop) -> "Type":
        return self.typ.unop_type(unop)

    def unop(self, unop: ast.unaryop) -> plt.AST:
        return self.typ.unop(unop)

    def python_type(self):
        return self.typ.python_type()


@dataclass(frozen=True, unsafe_hash=True)
class IntegerType(AtomicType):
    def pluthon_type(self, skip_constructor: bool = False) -> str:
        return "int"

    def python_type(self):
        return "int"

    def constr_type(self) -> InstanceType:
        return InstanceType(PolymorphicFunctionType(IntImpl()))

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        if isinstance(o, BoolType):
            if isinstance(op, ast.Eq):
                # 1 == True
                # 0 == False
                # all other comparisons are False
                return OLambda(
                    ["x", "y"],
                    plt.Ite(
                        OVar("y"),
                        plt.EqualsInteger(OVar("x"), plt.Integer(1)),
                        plt.EqualsInteger(OVar("x"), plt.Integer(0)),
                    ),
                )
        if isinstance(o, IntegerType):
            if isinstance(op, ast.Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsInteger)
            if isinstance(op, ast.NotEq):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsInteger),
                            OVar("y"),
                            OVar("x"),
                        )
                    ),
                )
            if isinstance(op, ast.LtE):
                return plt.BuiltIn(uplc.BuiltInFun.LessThanEqualsInteger)
            if isinstance(op, ast.Lt):
                return plt.BuiltIn(uplc.BuiltInFun.LessThanInteger)
            if isinstance(op, ast.Gt):
                return OLambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.BuiltIn(uplc.BuiltInFun.LessThanInteger),
                        OVar("y"),
                        OVar("x"),
                    ),
                )
            if isinstance(op, ast.GtE):
                return OLambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.BuiltIn(uplc.BuiltInFun.LessThanEqualsInteger),
                        OVar("y"),
                        OVar("x"),
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and isinstance(o.typ.typ, IntegerType)
        ):
            if isinstance(op, ast.In):
                return OLambda(
                    ["x", "y"],
                    plt.AnyList(
                        OVar("y"),
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsInteger), OVar("x")
                        ),
                    ),
                )
            if isinstance(op, ast.NotIn):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.AnyList(
                            OVar("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsInteger), OVar("x")
                            ),
                        ),
                    ),
                )
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return OLambda(
            ["x"],
            plt.DecodeUtf8(
                OLet(
                    [
                        (
                            "strlist",
                            plt.RecFun(
                                OLambda(
                                    ["f", "i"],
                                    plt.Ite(
                                        plt.LessThanEqualsInteger(
                                            OVar("i"), plt.Integer(0)
                                        ),
                                        plt.EmptyIntegerList(),
                                        plt.MkCons(
                                            plt.AddInteger(
                                                plt.ModInteger(
                                                    OVar("i"), plt.Integer(10)
                                                ),
                                                plt.Integer(ord("0")),
                                            ),
                                            plt.Apply(
                                                OVar("f"),
                                                OVar("f"),
                                                plt.DivideInteger(
                                                    OVar("i"), plt.Integer(10)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "mkstr",
                            OLambda(
                                ["i"],
                                plt.FoldList(
                                    plt.Apply(OVar("strlist"), OVar("i")),
                                    OLambda(
                                        ["b", "i"],
                                        plt.ConsByteString(OVar("i"), OVar("b")),
                                    ),
                                    plt.ByteString(b""),
                                ),
                            ),
                        ),
                    ],
                    plt.Ite(
                        plt.EqualsInteger(OVar("x"), plt.Integer(0)),
                        plt.ByteString(b"0"),
                        plt.Ite(
                            plt.LessThanInteger(OVar("x"), plt.Integer(0)),
                            plt.ConsByteString(
                                plt.Integer(ord("-")),
                                plt.Apply(OVar("mkstr"), plt.Negate(OVar("x"))),
                            ),
                            plt.Apply(OVar("mkstr"), OVar("x")),
                        ),
                    ),
                )
            ),
        )

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        if isinstance(other, InstanceType) and isinstance(other.typ, RecordType):
            print("Ha")
        if (
            isinstance(binop, ast.Add)
            or isinstance(binop, ast.Sub)
            or isinstance(binop, ast.FloorDiv)
            or isinstance(binop, ast.Mod)
            or isinstance(binop, ast.Div)
            or isinstance(binop, ast.Pow)
        ):
            if other == IntegerInstanceType:
                return IntegerType()
            elif other == BoolInstanceType:
                # cast to integer
                return IntegerType()
        if isinstance(binop, ast.Mult):
            if other == IntegerInstanceType:
                return IntegerType()
            elif other == ByteStringInstanceType:
                return ByteStringType()
            elif other == StringInstanceType:
                return StringType()
        return super()._binop_return_type(binop, other)

    def _binop_bin_fun(self, binop: ast.operator, other: "TypedAST"):
        if other.typ == IntegerInstanceType:
            if isinstance(binop, ast.Add):
                return plt.AddInteger
            elif isinstance(binop, ast.Sub):
                return plt.SubtractInteger
            elif isinstance(binop, ast.FloorDiv):
                return plt.DivideInteger
            elif isinstance(binop, ast.Mod):
                return plt.ModInteger
            elif isinstance(binop, ast.Pow):
                return lambda x, y: OLet(
                    [("y", y)],
                    plt.Ite(
                        plt.LessThanInteger(OVar("y"), plt.Integer(0)),
                        plt.TraceError("Negative exponentiation is not supported"),
                        PowImpl(x, OVar("y")),
                    ),
                )
        if other.typ == BoolInstanceType:
            if isinstance(binop, ast.Add):
                return lambda x, y: OLet(
                    [("x", x), ("y", y)],
                    plt.Ite(
                        OVar("y"), plt.AddInteger(OVar("x"), plt.Integer(1)), OVar("x")
                    ),
                )
            elif isinstance(binop, ast.Sub):
                return lambda x, y: OLet(
                    [("x", x), ("y", y)],
                    plt.Ite(
                        OVar("y"),
                        plt.SubtractInteger(OVar("x"), plt.Integer(1)),
                        OVar("x"),
                    ),
                )

        if isinstance(binop, ast.Mult):
            if other.typ == IntegerInstanceType:
                return plt.MultiplyInteger
            elif other.typ == ByteStringInstanceType:
                return lambda x, y: ByteStrIntMulImpl(y, x)
            elif other.typ == StringInstanceType:
                return lambda x, y: StrIntMulImpl(y, x)
        return super()._binop_bin_fun(binop, other)

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, ast.USub):
            return IntegerType()
        elif isinstance(unop, ast.UAdd):
            return IntegerType()
        elif isinstance(unop, ast.Not):
            return BoolType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop) -> Callable[[plt.AST], plt.AST]:
        if isinstance(unop, ast.USub):
            return lambda x: plt.SubtractInteger(plt.Integer(0), x)
        if isinstance(unop, ast.UAdd):
            return lambda x: x
        if isinstance(unop, ast.Not):
            return lambda x: plt.EqualsInteger(x, plt.Integer(0))
        return super()._unop_fun(unop)

    def copy_only_attributes(self) -> plt.AST:
        return OLambda(
            ["self"],
            plt.DelayedChooseData(
                OVar("self"),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusInteger but got PlutusData"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusInteger but got PlutusMap"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusInteger but got PlutusList"
                ),
                OVar("self"),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusInteger but got PlutusByteString"
                ),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class StringType(AtomicType):

    def python_type(self):
        return "str"

    def constr_type(self) -> InstanceType:
        return InstanceType(PolymorphicFunctionType(StrImpl()))

    def attribute_type(self, attr) -> Type:
        if attr == "encode":
            return InstanceType(FunctionType(frozenlist([]), ByteStringInstanceType))
        return super().attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        if attr == "encode":
            # No codec -> only the default (utf8) is allowed
            return OLambda(["x", "_"], plt.EncodeUtf8(OVar("x")))
        return super().attribute(attr)

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        if isinstance(o, StringType):
            if isinstance(op, ast.Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsString)
            if isinstance(op, ast.NotEq):
                return OLambda(
                    ["x", "y"], plt.Not(plt.EqualsString(OVar("x"), OVar("y")))
                )
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        if recursive:
            # TODO this is not correct, as the string is not properly escaped
            return OLambda(
                ["self"],
                plt.ConcatString(plt.Text("'"), OVar("self"), plt.Text("'")),
            )
        else:
            return OLambda(["self"], OVar("self"))

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        if isinstance(binop, ast.Add):
            if other == StringInstanceType:
                return StringType()
        if isinstance(binop, ast.Mult):
            if other == IntegerInstanceType:
                return StringType()
        return super()._binop_return_type(binop, other)

    def _binop_bin_fun(self, binop: ast.operator, other: "TypedAST"):
        if isinstance(binop, ast.Add):
            if other.typ == StringInstanceType:
                return plt.AppendString
        if isinstance(binop, ast.Mult):
            if other.typ == IntegerInstanceType:
                return StrIntMulImpl
        return super()._binop_bin_fun(binop, other)

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, ast.Not):
            return BoolType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop) -> Callable[[plt.AST], plt.AST]:
        if isinstance(unop, ast.Not):
            return lambda x: plt.EqualsInteger(
                plt.LengthOfByteString(plt.EncodeUtf8(x)), plt.Integer(0)
            )
        return super()._unop_fun(unop)

    def copy_only_attributes(self) -> plt.AST:
        return OLambda(
            ["self"],
            plt.DelayedChooseData(
                OVar("self"),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteString but got PlutusData"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteString but got PlutusMap"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteString but got PlutusList"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteString but got PlutusInteger"
                ),
                OVar("self"),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class ByteStringType(AtomicType):
    def pluthon_type(self, skip_constructor: bool = False) -> str:
        return "bytes"

    def python_type(self):
        return "bytes"

    def constr_type(self) -> InstanceType:
        return InstanceType(PolymorphicFunctionType(BytesImpl()))

    def attribute_type(self, attr) -> Type:
        if attr == "decode":
            return InstanceType(FunctionType(frozenlist([]), StringInstanceType))
        if attr == "hex":
            return InstanceType(FunctionType(frozenlist([]), StringInstanceType))
        if attr == "fromhex":
            return InstanceType(
                FunctionType(
                    frozenlist([StringInstanceType]),
                    ByteStringInstanceType,
                )
            )
        return super().attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        if attr == "decode":
            # No codec -> only the default (utf8) is allowed
            return OLambda(["x", "_"], plt.DecodeUtf8(OVar("x")))
        if attr == "hex":
            return OLambda(
                ["x", "_"],
                plt.DecodeUtf8(
                    OLet(
                        [
                            (
                                "hexlist",
                                plt.RecFun(
                                    OLambda(
                                        ["f", "i"],
                                        plt.Ite(
                                            plt.LessThanInteger(
                                                OVar("i"), plt.Integer(0)
                                            ),
                                            plt.EmptyIntegerList(),
                                            plt.MkCons(
                                                plt.IndexByteString(
                                                    OVar("x"), OVar("i")
                                                ),
                                                plt.Apply(
                                                    OVar("f"),
                                                    OVar("f"),
                                                    plt.SubtractInteger(
                                                        OVar("i"), plt.Integer(1)
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            (
                                "map_str",
                                OLambda(
                                    ["i"],
                                    plt.AddInteger(
                                        OVar("i"),
                                        plt.IfThenElse(
                                            plt.LessThanInteger(
                                                OVar("i"), plt.Integer(10)
                                            ),
                                            plt.Integer(ord("0")),
                                            plt.Integer(ord("a") - 10),
                                        ),
                                    ),
                                ),
                            ),
                            (
                                "mkstr",
                                OLambda(
                                    ["i"],
                                    plt.FoldList(
                                        plt.Apply(OVar("hexlist"), OVar("i")),
                                        OLambda(
                                            ["b", "i"],
                                            plt.ConsByteString(
                                                plt.Apply(
                                                    OVar("map_str"),
                                                    plt.DivideInteger(
                                                        OVar("i"), plt.Integer(16)
                                                    ),
                                                ),
                                                plt.ConsByteString(
                                                    plt.Apply(
                                                        OVar("map_str"),
                                                        plt.ModInteger(
                                                            OVar("i"),
                                                            plt.Integer(16),
                                                        ),
                                                    ),
                                                    OVar("b"),
                                                ),
                                            ),
                                        ),
                                        plt.ByteString(b""),
                                    ),
                                ),
                            ),
                        ],
                        plt.Apply(
                            OVar("mkstr"),
                            plt.SubtractInteger(
                                plt.LengthOfByteString(OVar("x")), plt.Integer(1)
                            ),
                        ),
                    ),
                ),
            )
        if attr == "fromhex":
            return OLambda(
                ["_", "x"],
                OLet(
                    [
                        (
                            "bytestr",
                            plt.EncodeUtf8(plt.Force(OVar("x"))),
                        ),
                        (
                            "bytestr_len",
                            plt.LengthOfByteString(OVar("bytestr")),
                        ),
                        (
                            "char_to_int",
                            OLambda(
                                ["c"],
                                plt.Ite(
                                    plt.And(
                                        plt.LessThanEqualsInteger(
                                            plt.Integer(ord("a")), OVar("c")
                                        ),
                                        plt.LessThanEqualsInteger(
                                            OVar("c"), plt.Integer(ord("f"))
                                        ),
                                    ),
                                    plt.AddInteger(
                                        plt.SubtractInteger(
                                            OVar("c"), plt.Integer(ord("a"))
                                        ),
                                        plt.Integer(10),
                                    ),
                                    plt.Ite(
                                        plt.And(
                                            plt.LessThanEqualsInteger(
                                                plt.Integer(ord("0")), OVar("c")
                                            ),
                                            plt.LessThanEqualsInteger(
                                                OVar("c"), plt.Integer(ord("9"))
                                            ),
                                        ),
                                        plt.SubtractInteger(
                                            OVar("c"), plt.Integer(ord("0"))
                                        ),
                                        plt.Ite(
                                            plt.And(
                                                plt.LessThanEqualsInteger(
                                                    plt.Integer(ord("A")), OVar("c")
                                                ),
                                                plt.LessThanEqualsInteger(
                                                    OVar("c"), plt.Integer(ord("F"))
                                                ),
                                            ),
                                            plt.AddInteger(
                                                plt.SubtractInteger(
                                                    OVar("c"), plt.Integer(ord("A"))
                                                ),
                                                plt.Integer(10),
                                            ),
                                            plt.TraceError("Invalid hex character"),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "splitlist",
                            plt.RecFun(
                                OLambda(
                                    ["f", "i"],
                                    plt.Ite(
                                        plt.LessThanInteger(
                                            OVar("bytestr_len"),
                                            plt.AddInteger(OVar("i"), plt.Integer(1)),
                                        ),
                                        plt.ByteString(b""),
                                        plt.Ite(
                                            plt.LessThanInteger(
                                                OVar("bytestr_len"),
                                                plt.AddInteger(
                                                    OVar("i"), plt.Integer(2)
                                                ),
                                            ),
                                            plt.TraceError("Invalid hex string"),
                                            OLet(
                                                [
                                                    (
                                                        "char_at_i",
                                                        plt.IndexByteString(
                                                            OVar("bytestr"),
                                                            OVar("i"),
                                                        ),
                                                    ),
                                                    (
                                                        "char_at_ip1",
                                                        plt.IndexByteString(
                                                            OVar("bytestr"),
                                                            plt.AddInteger(
                                                                OVar("i"),
                                                                plt.Integer(1),
                                                            ),
                                                        ),
                                                    ),
                                                ],
                                                plt.ConsByteString(
                                                    plt.AddInteger(
                                                        plt.MultiplyInteger(
                                                            plt.Apply(
                                                                OVar("char_to_int"),
                                                                OVar("char_at_i"),
                                                            ),
                                                            plt.Integer(16),
                                                        ),
                                                        plt.Apply(
                                                            OVar("char_to_int"),
                                                            OVar("char_at_ip1"),
                                                        ),
                                                    ),
                                                    plt.Apply(
                                                        OVar("f"),
                                                        OVar("f"),
                                                        plt.AddInteger(
                                                            OVar("i"),
                                                            plt.Integer(2),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                )
                            ),
                        ),
                    ],
                    plt.Apply(OVar("splitlist"), plt.Integer(0)),
                ),
            )
        return super().attribute(attr)

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        if isinstance(o, ByteStringType):
            if isinstance(op, ast.Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsByteString)
            if isinstance(op, ast.NotEq):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsByteString),
                            OVar("y"),
                            OVar("x"),
                        )
                    ),
                )
            if isinstance(op, ast.Lt):
                return plt.BuiltIn(uplc.BuiltInFun.LessThanByteString)
            if isinstance(op, ast.LtE):
                return plt.BuiltIn(uplc.BuiltInFun.LessThanEqualsByteString)
            if isinstance(op, ast.Gt):
                return OLambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.BuiltIn(uplc.BuiltInFun.LessThanByteString),
                        OVar("y"),
                        OVar("x"),
                    ),
                )
            if isinstance(op, ast.GtE):
                return OLambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.BuiltIn(uplc.BuiltInFun.LessThanEqualsByteString),
                        OVar("y"),
                        OVar("x"),
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and isinstance(o.typ.typ, ByteStringType)
        ):
            if isinstance(op, ast.In):
                return OLambda(
                    ["x", "y"],
                    plt.AnyList(
                        OVar("y"),
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsByteString),
                            OVar("x"),
                        ),
                    ),
                )
            if isinstance(op, ast.NotIn):
                return OLambda(
                    ["x", "y"],
                    plt.Not(
                        plt.AnyList(
                            OVar("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsByteString),
                                OVar("x"),
                            ),
                        ),
                    ),
                )
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return OLambda(
            ["x"],
            plt.DecodeUtf8(
                OLet(
                    [
                        (
                            "hexlist",
                            plt.RecFun(
                                OLambda(
                                    ["f", "i"],
                                    plt.Ite(
                                        plt.LessThanInteger(OVar("i"), plt.Integer(0)),
                                        plt.EmptyIntegerList(),
                                        plt.MkCons(
                                            plt.IndexByteString(OVar("x"), OVar("i")),
                                            plt.Apply(
                                                OVar("f"),
                                                OVar("f"),
                                                plt.SubtractInteger(
                                                    OVar("i"), plt.Integer(1)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "map_str",
                            OLambda(
                                ["i"],
                                plt.AddInteger(
                                    OVar("i"),
                                    plt.IfThenElse(
                                        plt.LessThanInteger(OVar("i"), plt.Integer(10)),
                                        plt.Integer(ord("0")),
                                        plt.Integer(ord("a") - 10),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "mkstr",
                            OLambda(
                                ["i"],
                                plt.FoldList(
                                    plt.Apply(OVar("hexlist"), OVar("i")),
                                    OLambda(
                                        ["b", "i"],
                                        plt.Ite(
                                            # ascii printable characters are kept unmodified
                                            plt.And(
                                                plt.LessThanEqualsInteger(
                                                    plt.Integer(0x20), OVar("i")
                                                ),
                                                plt.LessThanEqualsInteger(
                                                    OVar("i"), plt.Integer(0x7E)
                                                ),
                                            ),
                                            plt.Ite(
                                                plt.EqualsInteger(
                                                    OVar("i"),
                                                    plt.Integer(ord("\\")),
                                                ),
                                                plt.AppendByteString(
                                                    plt.ByteString(b"\\\\"),
                                                    OVar("b"),
                                                ),
                                                plt.Ite(
                                                    plt.EqualsInteger(
                                                        OVar("i"),
                                                        plt.Integer(ord("'")),
                                                    ),
                                                    plt.AppendByteString(
                                                        plt.ByteString(b"\\'"),
                                                        OVar("b"),
                                                    ),
                                                    plt.ConsByteString(
                                                        OVar("i"), OVar("b")
                                                    ),
                                                ),
                                            ),
                                            plt.Ite(
                                                plt.EqualsInteger(
                                                    OVar("i"), plt.Integer(ord("\t"))
                                                ),
                                                plt.AppendByteString(
                                                    plt.ByteString(b"\\t"), OVar("b")
                                                ),
                                                plt.Ite(
                                                    plt.EqualsInteger(
                                                        OVar("i"),
                                                        plt.Integer(ord("\n")),
                                                    ),
                                                    plt.AppendByteString(
                                                        plt.ByteString(b"\\n"),
                                                        OVar("b"),
                                                    ),
                                                    plt.Ite(
                                                        plt.EqualsInteger(
                                                            OVar("i"),
                                                            plt.Integer(ord("\r")),
                                                        ),
                                                        plt.AppendByteString(
                                                            plt.ByteString(b"\\r"),
                                                            OVar("b"),
                                                        ),
                                                        plt.AppendByteString(
                                                            plt.ByteString(b"\\x"),
                                                            plt.ConsByteString(
                                                                plt.Apply(
                                                                    OVar("map_str"),
                                                                    plt.DivideInteger(
                                                                        OVar("i"),
                                                                        plt.Integer(16),
                                                                    ),
                                                                ),
                                                                plt.ConsByteString(
                                                                    plt.Apply(
                                                                        OVar("map_str"),
                                                                        plt.ModInteger(
                                                                            OVar("i"),
                                                                            plt.Integer(
                                                                                16
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    OVar("b"),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    plt.ByteString(b""),
                                ),
                            ),
                        ),
                    ],
                    plt.ConcatByteString(
                        plt.ByteString(b"b'"),
                        plt.Apply(
                            OVar("mkstr"),
                            plt.SubtractInteger(
                                plt.LengthOfByteString(OVar("x")), plt.Integer(1)
                            ),
                        ),
                        plt.ByteString(b"'"),
                    ),
                ),
            ),
        )

    def _binop_return_type(self, binop: ast.operator, other: "Type") -> "Type":
        if isinstance(binop, ast.Add):
            if other == ByteStringInstanceType:
                return ByteStringType()
        if isinstance(binop, ast.Mult):
            if other == IntegerInstanceType:
                return ByteStringType()
        return super()._binop_return_type(binop, other)

    def _binop_bin_fun(self, binop: ast.operator, other: "TypedAST"):
        if isinstance(binop, ast.Add):
            if other.typ == ByteStringInstanceType:
                return plt.AppendByteString
        if isinstance(binop, ast.Mult):
            if other.typ == IntegerInstanceType:
                return ByteStrIntMulImpl
        return super()._binop_bin_fun(binop, other)

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, ast.Not):
            return BoolType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop) -> Callable[[plt.AST], plt.AST]:
        if isinstance(unop, ast.Not):
            return lambda x: plt.EqualsInteger(
                plt.LengthOfByteString(x), plt.Integer(0)
            )
        return super()._unop_fun(unop)

    def copy_only_attributes(self) -> plt.AST:
        return OLambda(
            ["self"],
            plt.DelayedChooseData(
                OVar("self"),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteString but got PlutusData"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteString but got PlutusMap"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteString but got PlutusList"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteString but got PlutusInteger"
                ),
                OVar("self"),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class BoolType(AtomicType):

    def python_type(self):
        return "bool"

    def constr_type(self) -> "InstanceType":
        return InstanceType(PolymorphicFunctionType(BoolImpl()))

    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        if isinstance(o, IntegerType):
            if isinstance(op, ast.Eq):
                # 1 == True
                # 0 == False
                # all other comparisons are False
                return OLambda(
                    ["y", "x"],
                    plt.Ite(
                        OVar("y"),
                        plt.EqualsInteger(OVar("x"), plt.Integer(1)),
                        plt.EqualsInteger(OVar("x"), plt.Integer(0)),
                    ),
                )
            if isinstance(op, ast.NotEq):
                return OLambda(
                    ["y", "x"],
                    plt.Ite(
                        OVar("y"),
                        plt.NotEqualsInteger(OVar("x"), plt.Integer(1)),
                        plt.NotEqualsInteger(OVar("x"), plt.Integer(0)),
                    ),
                )
        if isinstance(o, BoolType):
            if isinstance(op, ast.Eq):
                return OLambda(["x", "y"], plt.Iff(OVar("x"), OVar("y")))
            if isinstance(op, ast.NotEq):
                return OLambda(["x", "y"], plt.Not(plt.Iff(OVar("x"), OVar("y"))))
            if isinstance(op, ast.Lt):
                return OLambda(["x", "y"], plt.And(plt.Not(OVar("x")), OVar("y")))
            if isinstance(op, ast.Gt):
                return OLambda(["x", "y"], plt.And(OVar("x"), plt.Not(OVar("y"))))
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return OLambda(
            ["self"],
            plt.Ite(
                OVar("self"),
                plt.Text("True"),
                plt.Text("False"),
            ),
        )

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, ast.Not):
            return BoolType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop) -> Callable[[plt.AST], plt.AST]:
        if isinstance(unop, ast.Not):
            return plt.Not
        return super()._unop_fun(unop)

    def copy_only_attributes(self) -> plt.AST:
        return OLambda(
            ["self"],
            plt.DelayedChooseData(
                OVar("self"),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteInteger but got PlutusData"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteInteger but got PlutusMap"
                ),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteInteger but got PlutusList"
                ),
                OVar("self"),
                plt.TraceError(
                    f"IntegrityError: Expected PlutusByteInteger but got PlutusByteString"
                ),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class UnitType(AtomicType):
    def cmp(self, op: ast.cmpop, o: "Type") -> plt.AST:
        if isinstance(o, UnitType):
            if isinstance(op, ast.Eq):
                return OLambda(["x", "y"], plt.Bool(True))
            if isinstance(op, ast.NotEq):
                return OLambda(["x", "y"], plt.Bool(False))
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return OLambda(["self"], plt.Text("None"))

    def _unop_return_type(self, unop: ast.unaryop) -> "Type":
        if isinstance(unop, ast.Not):
            return BoolType()
        return super()._unop_return_type(unop)

    def _unop_fun(self, unop: ast.unaryop) -> Callable[[plt.AST], plt.AST]:
        if isinstance(unop, ast.Not):
            return lambda x: plt.Bool(True)
        return super()._unop_fun(unop)

    def python_type(self):
        return "None"


IntegerInstanceType = InstanceType(IntegerType())
StringInstanceType = InstanceType(StringType())
ByteStringInstanceType = InstanceType(ByteStringType())
BoolInstanceType = InstanceType(BoolType())
UnitInstanceType = InstanceType(UnitType())

ATOMIC_TYPES = {
    int.__name__: IntegerType(),
    str.__name__: StringType(),
    bytes.__name__: ByteStringType(),
    bytearray.__name__: ByteStringType(),
    type(None).__name__: UnitType(),
    bool.__name__: BoolType(),
}


NoneInstanceType = UnitInstanceType


class InaccessibleType(ClassType):
    """A type that blocks overwriting of a function"""

    pass

    def python_type(self):
        return "<forbidden>"


def repeated_addition(zero, add):
    # this is optimized for logarithmic complexity by exponentiation by squaring
    # it follows the implementation described here: https://en.wikipedia.org/wiki/Exponentiation_by_squaring#With_constant_auxiliary_memory
    def RepeatedAdd(x: plt.AST, y: plt.AST):
        return plt.Apply(
            plt.RecFun(
                OLambda(
                    ["f", "y", "x", "n"],
                    plt.Ite(
                        plt.LessThanEqualsInteger(OVar("n"), plt.Integer(0)),
                        OVar("y"),
                        OLet(
                            [
                                (
                                    "n_half",
                                    plt.DivideInteger(OVar("n"), plt.Integer(2)),
                                )
                            ],
                            plt.Ite(
                                # tests whether (x//2)*2 == x which is True iff x is even
                                plt.EqualsInteger(
                                    plt.AddInteger(OVar("n_half"), OVar("n_half")),
                                    OVar("n"),
                                ),
                                plt.Apply(
                                    OVar("f"),
                                    OVar("f"),
                                    OVar("y"),
                                    add(OVar("x"), OVar("x")),
                                    OVar("n_half"),
                                ),
                                plt.Apply(
                                    OVar("f"),
                                    OVar("f"),
                                    add(OVar("y"), OVar("x")),
                                    add(OVar("x"), OVar("x")),
                                    OVar("n_half"),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            zero,
            x,
            y,
        )

    return RepeatedAdd


PowImpl = repeated_addition(plt.Integer(1), plt.MultiplyInteger)
ByteStrIntMulImpl = repeated_addition(plt.ByteString(b""), plt.AppendByteString)
StrIntMulImpl = repeated_addition(plt.Text(""), plt.AppendString)


class PolymorphicFunction:
    def __new__(meta, *args, **kwargs):
        klass = super().__new__(meta)

        for key in ["impl_from_args"]:
            value = getattr(klass, key)
            wrapped = patternize(value)
            object.__setattr__(klass, key, wrapped)

        return klass

    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        raise NotImplementedError()

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        raise NotImplementedError()


class StrImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 1
        ), f"'str' takes only one argument, but {len(args)} were given"
        typ = args[0]
        assert isinstance(typ, InstanceType), "Can only stringify instances"
        return FunctionType(args, StringInstanceType)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(arg, InstanceType), "Can only stringify instances"
        return arg.typ.stringify()


class IntImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 1
        ), f"'int' takes only one argument, but {len(args)} were given"
        typ = args[0]
        assert isinstance(typ, InstanceType), "Can only create ints from instances"
        assert any(
            isinstance(typ.typ, t) for t in (IntegerType, StringType, BoolType)
        ), "Can only create integers from int, str or bool"
        return FunctionType(args, IntegerInstanceType)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(arg, InstanceType), "Can only create ints from instances"
        if isinstance(arg.typ, IntegerType):
            return OLambda(["x"], OVar("x"))
        elif isinstance(arg.typ, BoolType):
            return OLambda(
                ["x"], plt.IfThenElse(OVar("x"), plt.Integer(1), plt.Integer(0))
            )
        elif isinstance(arg.typ, StringType):
            return OLambda(
                ["x"],
                OLet(
                    [
                        ("e", plt.EncodeUtf8(OVar("x"))),
                        ("len", plt.LengthOfByteString(OVar("e"))),
                        (
                            "first_int",
                            plt.Ite(
                                plt.LessThanInteger(plt.Integer(0), OVar("len")),
                                plt.IndexByteString(OVar("e"), plt.Integer(0)),
                                plt.Integer(ord("_")),
                            ),
                        ),
                        (
                            "last_int",
                            plt.IndexByteString(
                                OVar("e"),
                                plt.SubtractInteger(OVar("len"), plt.Integer(1)),
                            ),
                        ),
                        (
                            "fold_start",
                            OLambda(
                                ["start"],
                                plt.FoldList(
                                    plt.Range(OVar("len"), OVar("start")),
                                    OLambda(
                                        ["s", "i"],
                                        OLet(
                                            [
                                                (
                                                    "b",
                                                    plt.IndexByteString(
                                                        OVar("e"), OVar("i")
                                                    ),
                                                )
                                            ],
                                            plt.Ite(
                                                plt.EqualsInteger(
                                                    OVar("b"), plt.Integer(ord("_"))
                                                ),
                                                OVar("s"),
                                                plt.Ite(
                                                    plt.Or(
                                                        plt.LessThanInteger(
                                                            OVar("b"),
                                                            plt.Integer(ord("0")),
                                                        ),
                                                        plt.LessThanInteger(
                                                            plt.Integer(ord("9")),
                                                            OVar("b"),
                                                        ),
                                                    ),
                                                    plt.TraceError(
                                                        "ValueError: invalid literal for int() with base 10"
                                                    ),
                                                    plt.AddInteger(
                                                        plt.SubtractInteger(
                                                            OVar("b"),
                                                            plt.Integer(ord("0")),
                                                        ),
                                                        plt.MultiplyInteger(
                                                            OVar("s"),
                                                            plt.Integer(10),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                    plt.Integer(0),
                                ),
                            ),
                        ),
                    ],
                    plt.Ite(
                        plt.Or(
                            plt.Or(
                                plt.EqualsInteger(
                                    OVar("first_int"),
                                    plt.Integer(ord("_")),
                                ),
                                plt.EqualsInteger(
                                    OVar("last_int"),
                                    plt.Integer(ord("_")),
                                ),
                            ),
                            plt.And(
                                plt.EqualsInteger(OVar("len"), plt.Integer(1)),
                                plt.Or(
                                    plt.EqualsInteger(
                                        OVar("first_int"),
                                        plt.Integer(ord("-")),
                                    ),
                                    plt.EqualsInteger(
                                        OVar("first_int"),
                                        plt.Integer(ord("+")),
                                    ),
                                ),
                            ),
                        ),
                        plt.TraceError(
                            "ValueError: invalid literal for int() with base 10"
                        ),
                        plt.Ite(
                            plt.EqualsInteger(
                                OVar("first_int"),
                                plt.Integer(ord("-")),
                            ),
                            plt.Negate(
                                plt.Apply(OVar("fold_start"), plt.Integer(1)),
                            ),
                            plt.Ite(
                                plt.EqualsInteger(
                                    OVar("first_int"),
                                    plt.Integer(ord("+")),
                                ),
                                plt.Apply(OVar("fold_start"), plt.Integer(1)),
                                plt.Apply(OVar("fold_start"), plt.Integer(0)),
                            ),
                        ),
                    ),
                ),
            )
        else:
            raise NotImplementedError(
                f"Can not derive integer from type {arg.typ.python_type()}"
            )


class BoolImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 1
        ), f"'bool' takes only one argument, but {len(args)} were given"
        typ = args[0]
        assert isinstance(typ, InstanceType), "Can only create bools from instances"
        assert any(
            isinstance(typ.typ, t)
            for t in (
                IntegerType,
                StringType,
                ByteStringType,
                BoolType,
                UnitType,
                ListType,
                DictType,
            )
        ), "Can only create bools from int, str, bool, bytes, None, list or dict"
        return FunctionType(args, BoolInstanceType)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(arg, InstanceType), "Can only create bools from instances"
        if isinstance(arg.typ, BoolType):
            return OLambda(["x"], OVar("x"))
        elif isinstance(arg.typ, IntegerType):
            return OLambda(["x"], plt.NotEqualsInteger(OVar("x"), plt.Integer(0)))
        elif isinstance(arg.typ, StringType):
            return OLambda(
                ["x"],
                plt.NotEqualsInteger(
                    plt.LengthOfByteString(plt.EncodeUtf8(OVar("x"))), plt.Integer(0)
                ),
            )
        elif isinstance(arg.typ, ByteStringType):
            return OLambda(
                ["x"],
                plt.NotEqualsInteger(plt.LengthOfByteString(OVar("x")), plt.Integer(0)),
            )
        elif isinstance(arg.typ, ListType) or isinstance(arg.typ, DictType):
            return OLambda(["x"], plt.Not(plt.NullList(OVar("x"))))
        elif isinstance(arg.typ, UnitType):
            return OLambda(["x"], plt.Bool(False))
        else:
            raise NotImplementedError(
                f"Can not derive bool from type {arg.typ.python_type()}"
            )


class BytesImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 1
        ), f"'bytes' takes only one argument, but {len(args)} were given"
        typ = args[0]
        assert isinstance(
            typ, InstanceType
        ), "Can only create bytes from instances, got ClassType"
        assert any(
            isinstance(typ.typ, t)
            for t in (
                IntegerType,
                ByteStringType,
                ListType,
            )
        ), f"Can only create bytes from int, bytes or integer lists, got {typ.python_type()}"
        if isinstance(typ.typ, ListType):
            assert (
                typ.typ.typ == IntegerInstanceType
            ), f"Can only create bytes from integer lists but got a list with another type {typ.python_type()}"
        return FunctionType(args, ByteStringInstanceType)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(
            arg, InstanceType
        ), "Can only create bytes from instances, got ClassType"
        if isinstance(arg.typ, ByteStringType):
            return OLambda(["x"], OVar("x"))
        elif isinstance(arg.typ, IntegerType):
            return OLambda(
                ["x"],
                plt.Ite(
                    plt.LessThanInteger(OVar("x"), plt.Integer(0)),
                    plt.TraceError("ValueError: negative count"),
                    ByteStrIntMulImpl(plt.ByteString(b"\x00"), OVar("x")),
                ),
            )
        elif isinstance(arg.typ, ListType):
            return OLambda(
                ["xs"],
                plt.RFoldList(
                    OVar("xs"),
                    OLambda(["a", "x"], plt.ConsByteString(OVar("x"), OVar("a"))),
                    plt.ByteString(b""),
                ),
            )
        else:
            raise NotImplementedError(
                f"Can not derive bytes from type {arg.typ.python_type()}"
            )


@dataclass(frozen=True, unsafe_hash=True)
class PolymorphicFunctionType(ClassType):
    """A special type of builtin that may act differently on different parameters"""

    polymorphic_function: PolymorphicFunction

    def __ge__(self, other):
        return (
            isinstance(other, PolymorphicFunctionType)
            and self.polymorphic_function == other.polymorphic_function
        )

    def python_type(self):
        return (
            f"PolymorphicFunctionType({self.polymorphic_function.__class__.__name__})"
        )


@dataclass(frozen=True, unsafe_hash=True)
class PolymorphicFunctionInstanceType(InstanceType):
    typ: FunctionType
    polymorphic_function: PolymorphicFunction

    def python_type(self):
        return self.typ.python_type()


EmptyListMap = {
    IntegerInstanceType: plt.EmptyIntegerList(),
    ByteStringInstanceType: plt.EmptyByteStringList(),
    StringInstanceType: plt.EmptyTextList(),
    UnitInstanceType: plt.EmptyUnitList(),
    BoolInstanceType: plt.EmptyBoolList(),
}


def empty_list(p: Type):
    if p in EmptyListMap:
        return EmptyListMap[p]
    assert isinstance(p, InstanceType), "Can only create lists of instances"
    if isinstance(p.typ, ListType):
        el = empty_list(p.typ.typ)
        return plt.EmptyListList(uplc.BuiltinList([], el.sample_value))
    if isinstance(p.typ, DictType):
        return plt.EmptyListList(
            uplc.BuiltinList(
                [],
                uplc.BuiltinPair(
                    uplc.PlutusConstr(0, frozenlist([])),
                    uplc.PlutusConstr(0, frozenlist([])),
                ),
            )
        )
    if (
        isinstance(p.typ, RecordType)
        or isinstance(p.typ, AnyType)
        or isinstance(p.typ, UnionType)
    ):
        return plt.EmptyDataList()
    raise NotImplementedError(f"Empty lists of type {p} can't be constructed yet")


TransformExtParamsMap = {
    IntegerInstanceType: lambda x: plt.UnIData(x),
    ByteStringInstanceType: lambda x: plt.UnBData(x),
    StringInstanceType: lambda x: plt.DecodeUtf8(plt.UnBData(x)),
    UnitInstanceType: lambda x: plt.Apply(OLambda(["_"], plt.Unit())),
    BoolInstanceType: lambda x: plt.NotEqualsInteger(plt.UnIData(x), plt.Integer(0)),
}


def transform_ext_params_map(p: Type):
    assert isinstance(
        p, InstanceType
    ), "Can only transform instances, not classes as input"
    if p in TransformExtParamsMap:
        return TransformExtParamsMap[p]
    if isinstance(p.typ, ListType):
        list_int_typ = p.typ.typ
        return lambda x: plt.MapList(
            plt.UnListData(x),
            OLambda(["x"], transform_ext_params_map(list_int_typ)(OVar("x"))),
            empty_list(p.typ.typ),
        )
    if isinstance(p.typ, DictType):
        # there doesn't appear to be a constructor function to make Pair a b for any types
        # so pairs will always contain Data
        return lambda x: plt.UnMapData(x)
    return lambda x: x


OUnit = plt.ConstrData(plt.Integer(0), plt.EmptyDataList())

TransformOutputMap = {
    StringInstanceType: lambda x: plt.BData(plt.EncodeUtf8(x)),
    IntegerInstanceType: lambda x: plt.IData(x),
    ByteStringInstanceType: lambda x: plt.BData(x),
    UnitInstanceType: lambda x: plt.Apply(OLambda(["_"], OUnit), x),
    BoolInstanceType: lambda x: plt.IData(
        plt.IfThenElse(x, plt.Integer(1), plt.Integer(0))
    ),
}


def transform_output_map(p: Type):
    assert isinstance(
        p, InstanceType
    ), "Can only transform instances, not classes as input"
    if isinstance(p.typ, FunctionType) or isinstance(p.typ, PolymorphicFunction):
        raise NotImplementedError(
            "Can not map functions into PlutusData and hence not return them from a function as Anything"
        )
    if p in TransformOutputMap:
        return TransformOutputMap[p]
    if isinstance(p.typ, ListType):
        list_int_typ = p.typ.typ
        return lambda x: plt.ListData(
            plt.MapList(
                x,
                OLambda(["x"], transform_output_map(list_int_typ)(OVar("x"))),
            ),
        )
    if isinstance(p.typ, DictType):
        # there doesn't appear to be a constructor function to make Pair a b for any types
        # so pairs will always contain Data
        return lambda x: plt.MapData(x)
    return lambda x: x
