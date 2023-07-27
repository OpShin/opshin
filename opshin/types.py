import logging
from ast import *
from dataclasses import dataclass
import itertools

import pluthon as plt

from .util import *

_LOGGER = logging.getLogger(__name__)


class TypeInferenceError(AssertionError):
    pass


class Type:
    def constr_type(self) -> "InstanceType":
        """The type of the constructor for this class"""
        raise TypeInferenceError(
            f"Object of type {self.__class__} does not have a constructor"
        )

    def constr(self) -> plt.AST:
        """The constructor for this class"""
        raise NotImplementedError(f"Constructor of {self.__class__} not implemented")

    def attribute_type(self, attr) -> "Type":
        """The types of the named attributes of this class"""
        raise TypeInferenceError(
            f"Object of type {self.__class__} does not have attribute {attr}"
        )

    def attribute(self, attr) -> plt.AST:
        """The attributes of this class. Needs to be a lambda that expects as first argument the object itself"""
        raise NotImplementedError(f"Attribute {attr} not implemented for type {self}")

    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        raise NotImplementedError(
            f"Comparison {type(op).__name__} for {self.__class__.__name__} and {o.__class__.__name__} is not implemented. This is likely intended because it would always evaluate to False."
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        """
        Returns a stringified version of the object

        The recursive parameter informs the method whether it was invoked recursively from another invokation
        """
        raise NotImplementedError(f"{type(self).__name__} can not be stringified")


@dataclass(frozen=True, unsafe_hash=True)
class Record:
    name: str
    constructor: int
    fields: typing.Union[typing.List[typing.Tuple[str, Type]], frozenlist]

    def __ge__(self, other):
        if not isinstance(other, Record):
            return False
        return (
            self.constructor == other.constructor
            and len(self.fields) == len(other.fields)
            and all(a >= b for a, b in zip(self.fields, other.fields))
        )


@dataclass(frozen=True, unsafe_hash=True)
class ClassType(Type):
    def __ge__(self, other):
        raise NotImplementedError("Comparison between raw classtypes impossible")


@dataclass(frozen=True, unsafe_hash=True)
class AnyType(ClassType):
    """The top element in the partial order on types (excluding FunctionTypes, which do not compare to anything)"""

    def __ge__(self, other):
        return (
            isinstance(other, ClassType)
            and not isinstance(other, FunctionType)
            and not isinstance(other, PolymorphicFunctionType)
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        _LOGGER.warning(
            "Serializing AnyType will result in RawPlutusData (CBOR representation) to be printed without additional type information. Annotate types where possible to avoid this warning."
        )
        return plt.Lambda(
            ["self", "_"],
            plt.Let(
                [
                    (
                        "joinMapList",
                        plt.Lambda(
                            ["m", "l", "start", "end"],
                            plt.Let(
                                [
                                    (
                                        "g",
                                        plt.RecFun(
                                            plt.Lambda(
                                                ["f", "l"],
                                                plt.AppendString(
                                                    plt.Apply(
                                                        plt.Var("m"),
                                                        plt.HeadList(plt.Var("l")),
                                                    ),
                                                    plt.Let(
                                                        [
                                                            (
                                                                "t",
                                                                plt.TailList(
                                                                    plt.Var("l")
                                                                ),
                                                            )
                                                        ],
                                                        plt.IteNullList(
                                                            plt.Var("t"),
                                                            plt.Var("end"),
                                                            plt.AppendString(
                                                                plt.Text(", "),
                                                                plt.Apply(
                                                                    plt.Var("f"),
                                                                    plt.Var("f"),
                                                                    plt.Var("t"),
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
                                    plt.Var("start"),
                                    plt.IteNullList(
                                        plt.Var("l"),
                                        plt.Var("end"),
                                        plt.Apply(
                                            plt.Var("g"),
                                            plt.Var("l"),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    (
                        "stringifyPlutusData",
                        plt.RecFun(
                            plt.Lambda(
                                ["f", "d"],
                                plt.DelayedChooseData(
                                    plt.Var("d"),
                                    plt.Let(
                                        [
                                            (
                                                "constructor",
                                                plt.FstPair(
                                                    plt.UnConstrData(plt.Var("d"))
                                                ),
                                            )
                                        ],
                                        plt.Ite(
                                            plt.LessThanInteger(
                                                plt.Var("constructor"), plt.Integer(128)
                                            ),
                                            plt.ConcatString(
                                                plt.Text("CBORTag("),
                                                plt.Apply(
                                                    plt.Var("f"),
                                                    plt.Var("f"),
                                                    plt.IData(
                                                        plt.AddInteger(
                                                            plt.Var("constructor"),
                                                            plt.Ite(
                                                                plt.LessThanInteger(
                                                                    plt.Var(
                                                                        "constructor"
                                                                    ),
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
                                                    plt.Var("f"),
                                                    plt.Var("f"),
                                                    plt.ListData(
                                                        plt.SndPair(
                                                            plt.UnConstrData(
                                                                plt.Var("d")
                                                            )
                                                        )
                                                    ),
                                                ),
                                                plt.Text(")"),
                                            ),
                                            plt.ConcatString(
                                                plt.Text("CBORTag(102, "),
                                                plt.Apply(
                                                    plt.Var("f"),
                                                    plt.Var("f"),
                                                    plt.ListData(
                                                        plt.MkCons(
                                                            plt.IData(
                                                                plt.Var("constructor")
                                                            ),
                                                            plt.MkCons(
                                                                plt.ListData(
                                                                    plt.SndPair(
                                                                        plt.UnConstrData(
                                                                            plt.Var("d")
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
                                        plt.Var("joinMapList"),
                                        plt.Lambda(
                                            ["x"],
                                            plt.ConcatString(
                                                plt.Apply(
                                                    plt.Var("f"),
                                                    plt.Var("f"),
                                                    plt.FstPair(plt.Var("x")),
                                                ),
                                                plt.Text(": "),
                                                plt.Apply(
                                                    plt.Var("f"),
                                                    plt.Var("f"),
                                                    plt.SndPair(plt.Var("x")),
                                                ),
                                            ),
                                        ),
                                        plt.UnMapData(plt.Var("d")),
                                        plt.Text("{"),
                                        plt.Text("}"),
                                    ),
                                    plt.Apply(
                                        plt.Var("joinMapList"),
                                        plt.Lambda(
                                            ["x"],
                                            plt.Apply(
                                                plt.Var("f"),
                                                plt.Var("f"),
                                                plt.Var("x"),
                                            ),
                                        ),
                                        plt.UnListData(plt.Var("d")),
                                        plt.Text("["),
                                        plt.Text("]"),
                                    ),
                                    plt.Apply(
                                        IntegerInstanceType.stringify(recursive=True),
                                        plt.UnIData(plt.Var("d")),
                                        plt.Var("_"),
                                    ),
                                    plt.Apply(
                                        ByteStringInstanceType.stringify(
                                            recursive=True
                                        ),
                                        plt.UnBData(plt.Var("d")),
                                        plt.Var("_"),
                                    ),
                                ),
                            )
                        ),
                    ),
                ],
                plt.ConcatString(
                    plt.Text("RawPlutusData(data="),
                    plt.Apply(plt.Var("stringifyPlutusData"), plt.Var("self")),
                    plt.Text(")"),
                ),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class AtomicType(ClassType):
    def __ge__(self, other):
        # Can only substitute for its own type (also subtypes)
        return isinstance(other, self.__class__)


@dataclass(frozen=True, unsafe_hash=True)
class RecordType(ClassType):
    record: Record

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
                transform_output_map(t)(plt.Var(n)), build_constr_params
            )
        # then build a constr type with this PlutusData
        return plt.Lambda(
            [n for n, _ in self.record.fields] + ["_"],
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
        raise TypeInferenceError(
            f"Type {self.record.name} does not have attribute {attr}"
        )

    def attribute(self, attr: str) -> plt.AST:
        """The attributes of this class. Need to be a lambda that expects as first argument the object itself"""
        if attr == "CONSTR_ID":
            # access to constructor
            return plt.Lambda(
                ["self"],
                plt.Constructor(plt.Var("self")),
            )
        if attr in (n for n, t in self.record.fields):
            attr_typ = self.attribute_type(attr)
            pos = next(i for i, (n, _) in enumerate(self.record.fields) if n == attr)
            # access to normal fields
            return plt.Lambda(
                ["self"],
                transform_ext_params_map(attr_typ)(
                    plt.NthField(
                        plt.Var("self"),
                        plt.Integer(pos),
                    ),
                ),
            )
        if attr == "to_cbor":
            return plt.Lambda(
                ["self", "_"],
                plt.SerialiseData(
                    plt.Var("self"),
                ),
            )
        raise NotImplementedError(f"Attribute {attr} not implemented for type {self}")

    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        # this will reject comparisons that will always be false - most likely due to faults during programming
        if (
            isinstance(o, RecordType)
            and (self.record >= o.record or o.record >= self.record)
        ) or (isinstance(o, UnionType) and any(self >= o or self >= o for o in o.typs)):
            if isinstance(op, Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsData)
            if isinstance(op, NotEq):
                return plt.Lambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                            plt.Var("x"),
                            plt.Var("y"),
                        )
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and (o.typ.typ >= self or self >= o.typ.typ)
        ):
            if isinstance(op, In):
                return plt.Lambda(
                    ["x", "y"],
                    plt.EqualsData(
                        plt.Var("x"),
                        plt.FindList(
                            plt.Var("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsData), plt.Var("x")
                            ),
                            # this simply ensures the default is always unequal to the searched value
                            plt.ConstrData(
                                plt.AddInteger(
                                    plt.Constructor(plt.Var("x")), plt.Integer(1)
                                ),
                                plt.MkNilData(plt.Unit()),
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
                            plt.NthField(plt.Var("self"), plt.Integer(pos))
                        ),
                        plt.Var("_"),
                    ),
                    map_fields,
                )
                pos -= 1
            map_fields = plt.ConcatString(
                plt.Text(f"{self.record.fields[0][0]}="),
                plt.Apply(
                    self.record.fields[0][1].stringify(recursive=True),
                    transform_ext_params_map(self.record.fields[0][1])(
                        plt.NthField(plt.Var("self"), plt.Integer(pos))
                    ),
                    plt.Var("_"),
                ),
                map_fields,
            )
        return plt.Lambda(
            ["self", "_"],
            plt.AppendString(plt.Text(f"{self.record.name}("), map_fields),
        )


@dataclass(frozen=True, unsafe_hash=True)
class UnionType(ClassType):
    typs: typing.List[RecordType]

    def attribute_type(self, attr) -> "Type":
        if attr == "CONSTR_ID":
            return IntegerInstanceType
        # need to have a common field with the same name
        if all(attr in (n for n, t in x.record.fields) for x in self.typs):
            attr_types = set(
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
            return plt.Lambda(
                ["self"],
                plt.Constructor(plt.Var("self")),
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
                pos_decisor = plt.Integer(pos_constrs[-1][0])
                pos_constrs = pos_constrs[:-1]
            for pos, constrs in pos_constrs:
                assert constrs, "Found empty constructors for a position"
                constr_check = plt.EqualsInteger(
                    plt.Var("constr"), plt.Integer(constrs[0])
                )
                for constr in constrs[1:]:
                    constr_check = plt.Or(
                        plt.EqualsInteger(plt.Var("constr"), plt.Integer(constr)),
                        constr_check,
                    )
                pos_decisor = plt.Ite(
                    constr_check,
                    plt.Integer(pos),
                    pos_decisor,
                )
            return plt.Lambda(
                ["self"],
                transform_ext_params_map(attr_typ)(
                    plt.NthField(
                        plt.Var("self"),
                        plt.Let(
                            [("constr", plt.Constructor(plt.Var("self")))], pos_decisor
                        ),
                    ),
                ),
            )
        if attr == "to_cbor":
            return plt.Lambda(
                ["self", "_"],
                plt.SerialiseData(
                    plt.Var("self"),
                ),
            )
        raise NotImplementedError(f"Attribute {attr} not implemented for type {self}")

    def __ge__(self, other):
        if isinstance(other, UnionType):
            return all(any(t >= ot for ot in other.typs) for t in self.typs)
        return any(t >= other for t in self.typs)

    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        # this will reject comparisons that will always be false - most likely due to faults during programming
        # note we require that there is an overlapt between the possible types for unions
        if (isinstance(o, RecordType) and any(t >= o or o >= t for t in self.typs)) or (
            isinstance(o, UnionType)
            and any(t >= ot or t >= ot for t in self.typs for ot in o.typs)
        ):
            if isinstance(op, Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsData)
            if isinstance(op, NotEq):
                return plt.Lambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsData),
                            plt.Var("x"),
                            plt.Var("y"),
                        )
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and any(o.typ.typ >= t or t >= o.typ.typ for t in self.typs)
        ):
            if isinstance(op, In):
                return plt.Lambda(
                    ["x", "y"],
                    plt.EqualsData(
                        plt.Var("x"),
                        plt.FindList(
                            plt.Var("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsData), plt.Var("x")
                            ),
                            # this simply ensures the default is always unequal to the searched value
                            plt.ConstrData(
                                plt.AddInteger(
                                    plt.Constructor(plt.Var("x")), plt.Integer(1)
                                ),
                                plt.MkNilData(plt.Unit()),
                            ),
                        ),
                    ),
                )
        raise NotImplementedError(
            f"Can not compare {o} and {self} with operation {op.__class__}. Note that comparisons that always return false are also rejected."
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        decide_string_func = plt.TraceError("Invalid constructor id in Union")
        for t in self.typs:
            decide_string_func = plt.Ite(
                plt.EqualsInteger(plt.Var("c"), plt.Integer(t.record.constructor)),
                t.stringify(recursive=True),
                decide_string_func,
            )
        return plt.Lambda(
            ["self", "_"],
            plt.Let(
                [("c", plt.Constructor(plt.Var("self")))],
                plt.Apply(decide_string_func, plt.Var("self"), plt.Var("_")),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class TupleType(ClassType):
    typs: typing.List[Type]

    def __ge__(self, other):
        return isinstance(other, TupleType) and all(
            t >= ot for t, ot in zip(self.typs, other.typs)
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        if not self.typs:
            return plt.Lambda(
                ["self", "_"],
                plt.Text("()"),
            )
        elif len(self.typs) == 1:
            tuple_content = plt.ConcatString(
                plt.Apply(
                    self.typs[0].stringify(recursive=True),
                    plt.FunctionalTupleAccess(plt.Var("self"), 0, len(self.typs)),
                    plt.Var("_"),
                ),
                plt.Text(","),
            )
        else:
            tuple_content = plt.ConcatString(
                plt.Apply(
                    self.typs[0].stringify(recursive=True),
                    plt.FunctionalTupleAccess(plt.Var("self"), 0, len(self.typs)),
                    plt.Var("_"),
                ),
            )
            for i, t in enumerate(self.typs[1:], start=1):
                tuple_content = plt.ConcatString(
                    tuple_content,
                    plt.Text(", "),
                    plt.Apply(
                        t.stringify(recursive=True),
                        plt.FunctionalTupleAccess(plt.Var("self"), i, len(self.typs)),
                        plt.Var("_"),
                    ),
                )
        return plt.Lambda(
            ["self", "_"],
            plt.ConcatString(plt.Text("("), tuple_content, plt.Text(")")),
        )


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
                transform_ext_params_map(self.l_typ)(plt.FstPair(plt.Var("self"))),
                plt.Var("_"),
            ),
            plt.Text(", "),
            plt.Apply(
                self.r_typ.stringify(recursive=True),
                transform_ext_params_map(self.r_typ)(plt.SndPair(plt.Var("self"))),
                plt.Var("_"),
            ),
        )
        return plt.Lambda(
            ["self", "_"],
            plt.ConcatString(plt.Text("("), tuple_content, plt.Text(")")),
        )


@dataclass(frozen=True, unsafe_hash=True)
class ListType(ClassType):
    typ: Type

    def __ge__(self, other):
        return isinstance(other, ListType) and self.typ >= other.typ

    def stringify(self, recursive: bool = False) -> plt.AST:
        return plt.Lambda(
            ["self", "_"],
            plt.Let(
                [
                    (
                        "g",
                        plt.RecFun(
                            plt.Lambda(
                                ["f", "l"],
                                plt.AppendString(
                                    plt.Apply(
                                        self.typ.stringify(recursive=True),
                                        plt.HeadList(plt.Var("l")),
                                        plt.Var("_"),
                                    ),
                                    plt.Let(
                                        [("t", plt.TailList(plt.Var("l")))],
                                        plt.IteNullList(
                                            plt.Var("t"),
                                            plt.Text("]"),
                                            plt.AppendString(
                                                plt.Text(", "),
                                                plt.Apply(
                                                    plt.Var("f"),
                                                    plt.Var("f"),
                                                    plt.Var("t"),
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
                        plt.Var("self"),
                        plt.Text("]"),
                        plt.Apply(
                            plt.Var("g"),
                            plt.Var("self"),
                        ),
                    ),
                ),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class DictType(ClassType):
    key_typ: Type
    value_typ: Type

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
            return plt.Lambda(
                ["self", "key", "default", "_"],
                transform_ext_params_map(self.value_typ)(
                    plt.SndPair(
                        plt.FindList(
                            plt.Var("self"),
                            plt.Lambda(
                                ["x"],
                                plt.EqualsData(
                                    transform_output_map(self.key_typ)(plt.Var("key")),
                                    plt.FstPair(plt.Var("x")),
                                ),
                            ),
                            # this is a bit ugly... we wrap - only to later unwrap again
                            plt.MkPairData(
                                transform_output_map(self.key_typ)(plt.Var("key")),
                                transform_output_map(self.value_typ)(
                                    plt.Var("default")
                                ),
                            ),
                        ),
                    ),
                ),
            )
        if attr == "keys":
            return plt.Lambda(
                ["self", "_"],
                plt.MapList(
                    plt.Var("self"),
                    plt.Lambda(
                        ["x"],
                        transform_ext_params_map(self.key_typ)(
                            plt.FstPair(plt.Var("x"))
                        ),
                    ),
                    empty_list(self.key_typ),
                ),
            )
        if attr == "values":
            return plt.Lambda(
                ["self", "_"],
                plt.MapList(
                    plt.Var("self"),
                    plt.Lambda(
                        ["x"],
                        transform_ext_params_map(self.value_typ)(
                            plt.SndPair(plt.Var("x"))
                        ),
                    ),
                    empty_list(self.value_typ),
                ),
            )
        if attr == "items":
            return plt.Lambda(
                ["self", "_"],
                plt.Var("self"),
            )
        raise NotImplementedError(f"Attribute '{attr}' of Dict is unknown.")

    def __ge__(self, other):
        return (
            isinstance(other, DictType)
            and self.key_typ >= other.key_typ
            and self.value_typ >= other.value_typ
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        return plt.Lambda(
            ["self", "_"],
            plt.Let(
                [
                    (
                        "g",
                        plt.RecFun(
                            plt.Lambda(
                                ["f", "l"],
                                plt.Let(
                                    [
                                        ("h", plt.HeadList(plt.Var("l"))),
                                        ("t", plt.TailList(plt.Var("l"))),
                                    ],
                                    plt.ConcatString(
                                        plt.Apply(
                                            self.key_typ.stringify(recursive=True),
                                            transform_ext_params_map(self.key_typ)(
                                                plt.FstPair(plt.Var("h"))
                                            ),
                                            plt.Var("_"),
                                        ),
                                        plt.Text(": "),
                                        plt.Apply(
                                            self.value_typ.stringify(recursive=True),
                                            transform_ext_params_map(self.value_typ)(
                                                plt.SndPair(plt.Var("h"))
                                            ),
                                            plt.Var("_"),
                                        ),
                                        plt.IteNullList(
                                            plt.Var("t"),
                                            plt.Text("}"),
                                            plt.AppendString(
                                                plt.Text(", "),
                                                plt.Apply(
                                                    plt.Var("f"),
                                                    plt.Var("f"),
                                                    plt.Var("t"),
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
                        plt.Var("self"),
                        plt.Text("}"),
                        plt.Apply(
                            plt.Var("g"),
                            plt.Var("self"),
                        ),
                    ),
                ),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class FunctionType(ClassType):
    argtyps: typing.List[Type]
    rettyp: Type

    def __ge__(self, other):
        return (
            isinstance(other, FunctionType)
            and all(a >= oa for a, oa in zip(self.argtyps, other.argtyps))
            and other.rettyp >= self.rettyp
        )

    def stringify(self, recursive: bool = False) -> plt.AST:
        return plt.Lambda(["x", "_"], plt.Text("<function>"))


@dataclass(frozen=True, unsafe_hash=True)
class InstanceType(Type):
    typ: ClassType

    def constr_type(self) -> FunctionType:
        raise TypeInferenceError(f"Can not construct an instance {self}")

    def constr(self) -> plt.AST:
        raise NotImplementedError(f"Can not construct an instance {self}")

    def attribute_type(self, attr) -> Type:
        return self.typ.attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        return self.typ.attribute(attr)

    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        if isinstance(o, InstanceType):
            return self.typ.cmp(op, o.typ)
        return super().cmp(op, o)

    def __ge__(self, other):
        return isinstance(other, InstanceType) and self.typ >= other.typ

    def stringify(self, recursive: bool = False) -> plt.AST:
        return self.typ.stringify(recursive=recursive)


@dataclass(frozen=True, unsafe_hash=True)
class IntegerType(AtomicType):
    def constr_type(self) -> InstanceType:
        return InstanceType(PolymorphicFunctionType(IntImpl()))

    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        """The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison."""
        if isinstance(o, BoolType):
            if isinstance(op, Eq):
                # 1 == True
                # 0 == False
                # all other comparisons are False
                return plt.Lambda(
                    ["x", "y"],
                    plt.Ite(
                        plt.Var("y"),
                        plt.EqualsInteger(plt.Var("x"), plt.Integer(1)),
                        plt.EqualsInteger(plt.Var("x"), plt.Integer(0)),
                    ),
                )
        if isinstance(o, IntegerType):
            if isinstance(op, Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsInteger)
            if isinstance(op, NotEq):
                return plt.Lambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsInteger),
                            plt.Var("y"),
                            plt.Var("x"),
                        )
                    ),
                )
            if isinstance(op, LtE):
                return plt.BuiltIn(uplc.BuiltInFun.LessThanEqualsInteger)
            if isinstance(op, Lt):
                return plt.BuiltIn(uplc.BuiltInFun.LessThanInteger)
            if isinstance(op, Gt):
                return plt.Lambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.BuiltIn(uplc.BuiltInFun.LessThanInteger),
                        plt.Var("y"),
                        plt.Var("x"),
                    ),
                )
            if isinstance(op, GtE):
                return plt.Lambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.BuiltIn(uplc.BuiltInFun.LessThanEqualsInteger),
                        plt.Var("y"),
                        plt.Var("x"),
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and isinstance(o.typ.typ, IntegerType)
        ):
            if isinstance(op, In):
                return plt.Lambda(
                    ["x", "y"],
                    plt.EqualsInteger(
                        plt.Var("x"),
                        plt.FindList(
                            plt.Var("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsInteger), plt.Var("x")
                            ),
                            # this simply ensures the default is always unequal to the searched value
                            plt.AddInteger(plt.Var("x"), plt.Integer(1)),
                        ),
                    ),
                )
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return plt.Lambda(
            ["x", "_"],
            plt.DecodeUtf8(
                plt.Let(
                    [
                        (
                            "strlist",
                            plt.RecFun(
                                plt.Lambda(
                                    ["f", "i"],
                                    plt.Ite(
                                        plt.LessThanEqualsInteger(
                                            plt.Var("i"), plt.Integer(0)
                                        ),
                                        plt.EmptyIntegerList(),
                                        plt.MkCons(
                                            plt.AddInteger(
                                                plt.ModInteger(
                                                    plt.Var("i"), plt.Integer(10)
                                                ),
                                                plt.Integer(ord("0")),
                                            ),
                                            plt.Apply(
                                                plt.Var("f"),
                                                plt.Var("f"),
                                                plt.DivideInteger(
                                                    plt.Var("i"), plt.Integer(10)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "mkstr",
                            plt.Lambda(
                                ["i"],
                                plt.FoldList(
                                    plt.Apply(plt.Var("strlist"), plt.Var("i")),
                                    plt.Lambda(
                                        ["b", "i"],
                                        plt.ConsByteString(plt.Var("i"), plt.Var("b")),
                                    ),
                                    plt.ByteString(b""),
                                ),
                            ),
                        ),
                    ],
                    plt.Ite(
                        plt.EqualsInteger(plt.Var("x"), plt.Integer(0)),
                        plt.ByteString(b"0"),
                        plt.Ite(
                            plt.LessThanInteger(plt.Var("x"), plt.Integer(0)),
                            plt.ConsByteString(
                                plt.Integer(ord("-")),
                                plt.Apply(plt.Var("mkstr"), plt.Negate(plt.Var("x"))),
                            ),
                            plt.Apply(plt.Var("mkstr"), plt.Var("x")),
                        ),
                    ),
                )
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class StringType(AtomicType):
    def constr_type(self) -> InstanceType:
        return InstanceType(PolymorphicFunctionType(StrImpl()))

    def attribute_type(self, attr) -> Type:
        if attr == "encode":
            return InstanceType(FunctionType(frozenlist([]), ByteStringInstanceType))
        return super().attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        if attr == "encode":
            # No codec -> only the default (utf8) is allowed
            return plt.Lambda(["x", "_"], plt.EncodeUtf8(plt.Var("x")))
        return super().attribute(attr)

    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        if isinstance(o, StringType):
            if isinstance(op, Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsString)
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        if recursive:
            # TODO this is not correct, as the string is not properly escaped
            return plt.Lambda(
                ["self", "_"],
                plt.ConcatString(plt.Text("'"), plt.Var("self"), plt.Text("'")),
            )
        else:
            return plt.Lambda(["self", "_"], plt.Var("self"))


@dataclass(frozen=True, unsafe_hash=True)
class ByteStringType(AtomicType):
    def constr_type(self) -> InstanceType:
        return InstanceType(PolymorphicFunctionType(BytesImpl()))

    def attribute_type(self, attr) -> Type:
        if attr == "decode":
            return InstanceType(FunctionType(frozenlist([]), StringInstanceType))
        if attr == "hex":
            return InstanceType(FunctionType(frozenlist([]), StringInstanceType))
        return super().attribute_type(attr)

    def attribute(self, attr) -> plt.AST:
        if attr == "decode":
            # No codec -> only the default (utf8) is allowed
            return plt.Lambda(["x", "_"], plt.DecodeUtf8(plt.Var("x")))
        if attr == "hex":
            return plt.Lambda(
                ["x", "_"],
                plt.DecodeUtf8(
                    plt.Let(
                        [
                            (
                                "hexlist",
                                plt.RecFun(
                                    plt.Lambda(
                                        ["f", "i"],
                                        plt.Ite(
                                            plt.LessThanInteger(
                                                plt.Var("i"), plt.Integer(0)
                                            ),
                                            plt.EmptyIntegerList(),
                                            plt.MkCons(
                                                plt.IndexByteString(
                                                    plt.Var("x"), plt.Var("i")
                                                ),
                                                plt.Apply(
                                                    plt.Var("f"),
                                                    plt.Var("f"),
                                                    plt.SubtractInteger(
                                                        plt.Var("i"), plt.Integer(1)
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            (
                                "map_str",
                                plt.Lambda(
                                    ["i"],
                                    plt.AddInteger(
                                        plt.Var("i"),
                                        plt.IfThenElse(
                                            plt.LessThanInteger(
                                                plt.Var("i"), plt.Integer(10)
                                            ),
                                            plt.Integer(ord("0")),
                                            plt.Integer(ord("a") - 10),
                                        ),
                                    ),
                                ),
                            ),
                            (
                                "mkstr",
                                plt.Lambda(
                                    ["i"],
                                    plt.FoldList(
                                        plt.Apply(plt.Var("hexlist"), plt.Var("i")),
                                        plt.Lambda(
                                            ["b", "i"],
                                            plt.ConsByteString(
                                                plt.Apply(
                                                    plt.Var("map_str"),
                                                    plt.DivideInteger(
                                                        plt.Var("i"), plt.Integer(16)
                                                    ),
                                                ),
                                                plt.ConsByteString(
                                                    plt.Apply(
                                                        plt.Var("map_str"),
                                                        plt.ModInteger(
                                                            plt.Var("i"),
                                                            plt.Integer(16),
                                                        ),
                                                    ),
                                                    plt.Var("b"),
                                                ),
                                            ),
                                        ),
                                        plt.ByteString(b""),
                                    ),
                                ),
                            ),
                        ],
                        plt.Apply(
                            plt.Var("mkstr"),
                            plt.SubtractInteger(
                                plt.LengthOfByteString(plt.Var("x")), plt.Integer(1)
                            ),
                        ),
                    ),
                ),
            )
        return super().attribute(attr)

    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        if isinstance(o, ByteStringType):
            if isinstance(op, Eq):
                return plt.BuiltIn(uplc.BuiltInFun.EqualsByteString)
            if isinstance(op, NotEq):
                return plt.Lambda(
                    ["x", "y"],
                    plt.Not(
                        plt.Apply(
                            plt.BuiltIn(uplc.BuiltInFun.EqualsByteString),
                            plt.Var("y"),
                            plt.Var("x"),
                        )
                    ),
                )
            if isinstance(op, Lt):
                return plt.BuiltIn(uplc.BuiltInFun.LessThanByteString)
            if isinstance(op, LtE):
                return plt.BuiltIn(uplc.BuiltInFun.LessThanEqualsByteString)
            if isinstance(op, Gt):
                return plt.Lambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.BuiltIn(uplc.BuiltInFun.LessThanByteString),
                        plt.Var("y"),
                        plt.Var("x"),
                    ),
                )
            if isinstance(op, GtE):
                return plt.Lambda(
                    ["x", "y"],
                    plt.Apply(
                        plt.BuiltIn(uplc.BuiltInFun.LessThanEqualsByteString),
                        plt.Var("y"),
                        plt.Var("x"),
                    ),
                )
        if (
            isinstance(o, ListType)
            and isinstance(o.typ, InstanceType)
            and isinstance(o.typ.typ, ByteStringType)
        ):
            if isinstance(op, In):
                return plt.Lambda(
                    ["x", "y"],
                    plt.EqualsByteString(
                        plt.Var("x"),
                        plt.FindList(
                            plt.Var("y"),
                            plt.Apply(
                                plt.BuiltIn(uplc.BuiltInFun.EqualsByteString),
                                plt.Var("x"),
                            ),
                            # this simply ensures the default is always unequal to the searched value
                            plt.ConsByteString(plt.Integer(0), plt.Var("x")),
                        ),
                    ),
                )
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return plt.Lambda(
            ["x", "_"],
            plt.DecodeUtf8(
                plt.Let(
                    [
                        (
                            "hexlist",
                            plt.RecFun(
                                plt.Lambda(
                                    ["f", "i"],
                                    plt.Ite(
                                        plt.LessThanInteger(
                                            plt.Var("i"), plt.Integer(0)
                                        ),
                                        plt.EmptyIntegerList(),
                                        plt.MkCons(
                                            plt.IndexByteString(
                                                plt.Var("x"), plt.Var("i")
                                            ),
                                            plt.Apply(
                                                plt.Var("f"),
                                                plt.Var("f"),
                                                plt.SubtractInteger(
                                                    plt.Var("i"), plt.Integer(1)
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "map_str",
                            plt.Lambda(
                                ["i"],
                                plt.AddInteger(
                                    plt.Var("i"),
                                    plt.IfThenElse(
                                        plt.LessThanInteger(
                                            plt.Var("i"), plt.Integer(10)
                                        ),
                                        plt.Integer(ord("0")),
                                        plt.Integer(ord("a") - 10),
                                    ),
                                ),
                            ),
                        ),
                        (
                            "mkstr",
                            plt.Lambda(
                                ["i"],
                                plt.FoldList(
                                    plt.Apply(plt.Var("hexlist"), plt.Var("i")),
                                    plt.Lambda(
                                        ["b", "i"],
                                        plt.Ite(
                                            # ascii printable characters are kept unmodified
                                            plt.And(
                                                plt.LessThanEqualsInteger(
                                                    plt.Integer(0x20), plt.Var("i")
                                                ),
                                                plt.LessThanEqualsInteger(
                                                    plt.Var("i"), plt.Integer(0x7E)
                                                ),
                                            ),
                                            plt.Ite(
                                                plt.EqualsInteger(
                                                    plt.Var("i"),
                                                    plt.Integer(ord("\\")),
                                                ),
                                                plt.AppendByteString(
                                                    plt.ByteString(b"\\\\"),
                                                    plt.Var("b"),
                                                ),
                                                plt.Ite(
                                                    plt.EqualsInteger(
                                                        plt.Var("i"),
                                                        plt.Integer(ord("'")),
                                                    ),
                                                    plt.AppendByteString(
                                                        plt.ByteString(b"\\'"),
                                                        plt.Var("b"),
                                                    ),
                                                    plt.ConsByteString(
                                                        plt.Var("i"), plt.Var("b")
                                                    ),
                                                ),
                                            ),
                                            plt.Ite(
                                                plt.EqualsInteger(
                                                    plt.Var("i"), plt.Integer(ord("\t"))
                                                ),
                                                plt.AppendByteString(
                                                    plt.ByteString(b"\\t"), plt.Var("b")
                                                ),
                                                plt.Ite(
                                                    plt.EqualsInteger(
                                                        plt.Var("i"),
                                                        plt.Integer(ord("\n")),
                                                    ),
                                                    plt.AppendByteString(
                                                        plt.ByteString(b"\\n"),
                                                        plt.Var("b"),
                                                    ),
                                                    plt.Ite(
                                                        plt.EqualsInteger(
                                                            plt.Var("i"),
                                                            plt.Integer(ord("\r")),
                                                        ),
                                                        plt.AppendByteString(
                                                            plt.ByteString(b"\\r"),
                                                            plt.Var("b"),
                                                        ),
                                                        plt.AppendByteString(
                                                            plt.ByteString(b"\\x"),
                                                            plt.ConsByteString(
                                                                plt.Apply(
                                                                    plt.Var("map_str"),
                                                                    plt.DivideInteger(
                                                                        plt.Var("i"),
                                                                        plt.Integer(16),
                                                                    ),
                                                                ),
                                                                plt.ConsByteString(
                                                                    plt.Apply(
                                                                        plt.Var(
                                                                            "map_str"
                                                                        ),
                                                                        plt.ModInteger(
                                                                            plt.Var(
                                                                                "i"
                                                                            ),
                                                                            plt.Integer(
                                                                                16
                                                                            ),
                                                                        ),
                                                                    ),
                                                                    plt.Var("b"),
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
                            plt.Var("mkstr"),
                            plt.SubtractInteger(
                                plt.LengthOfByteString(plt.Var("x")), plt.Integer(1)
                            ),
                        ),
                        plt.ByteString(b"'"),
                    ),
                ),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class BoolType(AtomicType):
    def constr_type(self) -> "InstanceType":
        return InstanceType(PolymorphicFunctionType(BoolImpl()))

    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        if isinstance(o, IntegerType):
            if isinstance(op, Eq):
                # 1 == True
                # 0 == False
                # all other comparisons are False
                return plt.Lambda(
                    ["y", "x"],
                    plt.Ite(
                        plt.Var("y"),
                        plt.EqualsInteger(plt.Var("x"), plt.Integer(1)),
                        plt.EqualsInteger(plt.Var("x"), plt.Integer(0)),
                    ),
                )
        if isinstance(o, BoolType):
            if isinstance(op, Eq):
                return plt.Lambda(["x", "y"], plt.Iff(plt.Var("x"), plt.Var("y")))
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return plt.Lambda(
            ["self", "_"],
            plt.Ite(
                plt.Var("self"),
                plt.Text("True"),
                plt.Text("False"),
            ),
        )


@dataclass(frozen=True, unsafe_hash=True)
class UnitType(AtomicType):
    def cmp(self, op: cmpop, o: "Type") -> plt.AST:
        if isinstance(o, UnitType):
            if isinstance(op, Eq):
                return plt.Lambda(["x", "y"], plt.Bool(True))
            if isinstance(op, NotEq):
                return plt.Lambda(["x", "y"], plt.Bool(False))
        return super().cmp(op, o)

    def stringify(self, recursive: bool = False) -> plt.AST:
        return plt.Lambda(["self", "_"], plt.Text("None"))


IntegerInstanceType = InstanceType(IntegerType())
StringInstanceType = InstanceType(StringType())
ByteStringInstanceType = InstanceType(ByteStringType())
BoolInstanceType = InstanceType(BoolType())
UnitInstanceType = InstanceType(UnitType())

ATOMIC_TYPES = {
    int.__name__: IntegerType(),
    str.__name__: StringType(),
    bytes.__name__: ByteStringType(),
    type(None).__name__: UnitType(),
    bool.__name__: BoolType(),
}


NoneInstanceType = UnitInstanceType


class InaccessibleType(ClassType):
    """A type that blocks overwriting of a function"""

    pass


def repeated_addition(zero, add):
    # this is optimized for logarithmic complexity by exponentiation by squaring
    # it follows the implementation described here: https://en.wikipedia.org/wiki/Exponentiation_by_squaring#With_constant_auxiliary_memory
    def RepeatedAdd(x: plt.AST, y: plt.AST):
        return plt.Apply(
            plt.RecFun(
                plt.Lambda(
                    ["f", "y", "x", "n"],
                    plt.Ite(
                        plt.LessThanEqualsInteger(plt.Var("n"), plt.Integer(0)),
                        plt.Var("y"),
                        plt.Let(
                            [
                                (
                                    "n_half",
                                    plt.DivideInteger(plt.Var("n"), plt.Integer(2)),
                                )
                            ],
                            plt.Ite(
                                # tests whether (x//2)*2 == x which is True iff x is even
                                plt.EqualsInteger(
                                    plt.AddInteger(
                                        plt.Var("n_half"), plt.Var("n_half")
                                    ),
                                    plt.Var("n"),
                                ),
                                plt.Apply(
                                    plt.Var("f"),
                                    plt.Var("f"),
                                    plt.Var("y"),
                                    add(plt.Var("x"), plt.Var("x")),
                                    plt.Var("n_half"),
                                ),
                                plt.Apply(
                                    plt.Var("f"),
                                    plt.Var("f"),
                                    add(plt.Var("y"), plt.Var("x")),
                                    add(plt.Var("x"), plt.Var("x")),
                                    plt.Var("n_half"),
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
            return plt.Lambda(["x", "_"], plt.Var("x"))
        elif isinstance(arg.typ, BoolType):
            return plt.Lambda(
                ["x", "_"], plt.IfThenElse(plt.Var("x"), plt.Integer(1), plt.Integer(0))
            )
        elif isinstance(arg.typ, StringType):
            return plt.Lambda(
                ["x", "_"],
                plt.Let(
                    [
                        ("e", plt.EncodeUtf8(plt.Var("x"))),
                        ("len", plt.LengthOfByteString(plt.Var("e"))),
                        (
                            "first_int",
                            plt.Ite(
                                plt.LessThanInteger(plt.Integer(0), plt.Var("len")),
                                plt.IndexByteString(plt.Var("e"), plt.Integer(0)),
                                plt.Integer(ord("_")),
                            ),
                        ),
                        (
                            "last_int",
                            plt.IndexByteString(
                                plt.Var("e"),
                                plt.SubtractInteger(plt.Var("len"), plt.Integer(1)),
                            ),
                        ),
                        (
                            "fold_start",
                            plt.Lambda(
                                ["start"],
                                plt.FoldList(
                                    plt.Range(plt.Var("len"), plt.Var("start")),
                                    plt.Lambda(
                                        ["s", "i"],
                                        plt.Let(
                                            [
                                                (
                                                    "b",
                                                    plt.IndexByteString(
                                                        plt.Var("e"), plt.Var("i")
                                                    ),
                                                )
                                            ],
                                            plt.Ite(
                                                plt.EqualsInteger(
                                                    plt.Var("b"), plt.Integer(ord("_"))
                                                ),
                                                plt.Var("s"),
                                                plt.Ite(
                                                    plt.Or(
                                                        plt.LessThanInteger(
                                                            plt.Var("b"),
                                                            plt.Integer(ord("0")),
                                                        ),
                                                        plt.LessThanInteger(
                                                            plt.Integer(ord("9")),
                                                            plt.Var("b"),
                                                        ),
                                                    ),
                                                    plt.TraceError(
                                                        "ValueError: invalid literal for int() with base 10"
                                                    ),
                                                    plt.AddInteger(
                                                        plt.SubtractInteger(
                                                            plt.Var("b"),
                                                            plt.Integer(ord("0")),
                                                        ),
                                                        plt.MultiplyInteger(
                                                            plt.Var("s"),
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
                                    plt.Var("first_int"),
                                    plt.Integer(ord("_")),
                                ),
                                plt.EqualsInteger(
                                    plt.Var("last_int"),
                                    plt.Integer(ord("_")),
                                ),
                            ),
                            plt.And(
                                plt.EqualsInteger(plt.Var("len"), plt.Integer(1)),
                                plt.Or(
                                    plt.EqualsInteger(
                                        plt.Var("first_int"),
                                        plt.Integer(ord("-")),
                                    ),
                                    plt.EqualsInteger(
                                        plt.Var("first_int"),
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
                                plt.Var("first_int"),
                                plt.Integer(ord("-")),
                            ),
                            plt.Negate(
                                plt.Apply(plt.Var("fold_start"), plt.Integer(1)),
                            ),
                            plt.Ite(
                                plt.EqualsInteger(
                                    plt.Var("first_int"),
                                    plt.Integer(ord("+")),
                                ),
                                plt.Apply(plt.Var("fold_start"), plt.Integer(1)),
                                plt.Apply(plt.Var("fold_start"), plt.Integer(0)),
                            ),
                        ),
                    ),
                ),
            )
        else:
            raise NotImplementedError(
                f"Can not derive integer from type {arg.typ.__name__}"
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
            return plt.Lambda(["x", "_"], plt.Var("x"))
        elif isinstance(arg.typ, IntegerType):
            return plt.Lambda(
                ["x", "_"], plt.NotEqualsInteger(plt.Var("x"), plt.Integer(0))
            )
        elif isinstance(arg.typ, StringType):
            return plt.Lambda(
                ["x", "_"],
                plt.NotEqualsInteger(
                    plt.LengthOfByteString(plt.EncodeUtf8(plt.Var("x"))), plt.Integer(0)
                ),
            )
        elif isinstance(arg.typ, ByteStringType):
            return plt.Lambda(
                ["x", "_"],
                plt.NotEqualsInteger(
                    plt.LengthOfByteString(plt.Var("x")), plt.Integer(0)
                ),
            )
        elif isinstance(arg.typ, ListType) or isinstance(arg.typ, DictType):
            return plt.Lambda(["x", "_"], plt.Not(plt.NullList(plt.Var("x"))))
        elif isinstance(arg.typ, UnitType):
            return plt.Lambda(["x", "_"], plt.Bool(False))
        else:
            raise NotImplementedError(
                f"Can not derive bool from type {arg.typ.__name__}"
            )


class BytesImpl(PolymorphicFunction):
    def type_from_args(self, args: typing.List[Type]) -> FunctionType:
        assert (
            len(args) == 1
        ), f"'bytes' takes only one argument, but {len(args)} were given"
        typ = args[0]
        assert isinstance(typ, InstanceType), "Can only create bools from instances"
        assert any(
            isinstance(typ.typ, t)
            for t in (
                IntegerType,
                ByteStringType,
                ListType,
            )
        ), "Can only create bytes from int, bytes or integer lists"
        if isinstance(typ.typ, ListType):
            assert (
                typ.typ.typ == IntegerInstanceType
            ), "Can only create bytes from integer lists but got a list with another type"
        return FunctionType(args, ByteStringInstanceType)

    def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(arg, InstanceType), "Can only create bytes from instances"
        if isinstance(arg.typ, ByteStringType):
            return plt.Lambda(["x", "_"], plt.Var("x"))
        elif isinstance(arg.typ, IntegerType):
            return plt.Lambda(
                ["x", "_"],
                plt.Ite(
                    plt.LessThanInteger(plt.Var("x"), plt.Integer(0)),
                    plt.TraceError("ValueError: negative count"),
                    ByteStrIntMulImpl(plt.ByteString(b"\x00"), plt.Var("x")),
                ),
            )
        elif isinstance(arg.typ, ListType):
            return plt.Lambda(
                ["xs", "_"],
                plt.RFoldList(
                    plt.Var("xs"),
                    plt.Lambda(
                        ["a", "x"], plt.ConsByteString(plt.Var("x"), plt.Var("a"))
                    ),
                    plt.ByteString(b""),
                ),
            )
        else:
            raise NotImplementedError(
                f"Can not derive bytes from type {arg.typ.__name__}"
            )


@dataclass(frozen=True, unsafe_hash=True)
class PolymorphicFunctionType(ClassType):
    """A special type of builtin that may act differently on different parameters"""

    polymorphic_function: PolymorphicFunction


@dataclass(frozen=True, unsafe_hash=True)
class PolymorphicFunctionInstanceType(InstanceType):
    typ: FunctionType
    polymorphic_function: PolymorphicFunction


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
    UnitInstanceType: lambda x: plt.Apply(plt.Lambda(["_"], plt.Unit())),
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
            plt.Lambda(["x"], transform_ext_params_map(list_int_typ)(plt.Var("x"))),
            empty_list(p.typ.typ),
        )
    if isinstance(p.typ, DictType):
        # there doesn't appear to be a constructor function to make Pair a b for any types
        # so pairs will always contain Data
        return lambda x: plt.UnMapData(x)
    return lambda x: x


TransformOutputMap = {
    StringInstanceType: lambda x: plt.BData(plt.EncodeUtf8(x)),
    IntegerInstanceType: lambda x: plt.IData(x),
    ByteStringInstanceType: lambda x: plt.BData(x),
    UnitInstanceType: lambda x: plt.Apply(
        plt.Lambda(["_"], plt.ConstrData(plt.Integer(0), plt.EmptyDataList())), x
    ),
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
                plt.Lambda(["x"], transform_output_map(list_int_typ)(plt.Var("x"))),
            ),
        )
    if isinstance(p.typ, DictType):
        # there doesn't appear to be a constructor function to make Pair a b for any types
        # so pairs will always contain Data
        return lambda x: plt.MapData(x)
    return lambda x: x
