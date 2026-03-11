from ast import *
from typing import Optional

import pluthon as plt
from frozenlist2 import frozenlist

from ..typed_ast import RawPlutoExpr
from ..type_impls import (
    FunctionType,
    InstanceType,
    PolymorphicFunction,
    PolymorphicFunctionType,
    RawTupleType,
    RecordType,
    Type,
)
from ..util import CompilingNodeTransformer, OLambda, OVar

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class AstupleImpl(PolymorphicFunction):
    def type_from_args(self, args: list[Type]) -> FunctionType:
        assert len(args) == 1, f"'astuple' takes one argument, but {len(args)} were given"
        arg = args[0]
        assert isinstance(arg, InstanceType) and isinstance(
            arg.typ, RecordType
        ), f"'astuple' expects a dataclass instance, found {arg.python_type()}"
        return FunctionType(
            args,
            InstanceType(
                RawTupleType(
                    frozenlist([field_typ for _, field_typ in arg.typ.record.fields]),
                )
            ),
        )

    def impl_from_args(self, args: list[Type]) -> plt.AST:
        arg = args[0]
        assert isinstance(arg, InstanceType) and isinstance(
            arg.typ, RecordType
        ), "Can only convert dataclass instances with astuple"
        return OLambda(["x"], plt.Fields(OVar("x")))


ASTUPLE_TYPE = InstanceType(PolymorphicFunctionType(AstupleImpl()))


class RewriteImportDataclasses(CompilingNodeTransformer):
    step = "Resolving the import and usage of dataclass"

    def __init__(self):
        self.imports_dataclasses = False
        self.imports_astuple = False

    def visit_ImportFrom(self, node: ImportFrom):
        if node.module != "dataclasses":
            return node
        imported_names = {name.name for name in node.names}
        additional_assigns = []
        for imported_name in node.names:
            assert imported_name.name in {"dataclass", "astuple"}, (
                "Only 'dataclass' and 'astuple' may be imported from dataclasses"
            )
            if imported_name.name == "dataclass":
                assert (
                    imported_name.asname == None
                ), "Imports of dataclass from dataclasses cannot be aliased"
            else:
                target_name = imported_name.asname or "astuple"
                additional_assigns.append(
                    Assign(
                        targets=[
                            Name(
                                id=target_name,
                                typ=ASTUPLE_TYPE,
                                ctx=Store(),
                            )
                        ],
                        value=RawPlutoExpr(
                            typ=ASTUPLE_TYPE,
                            expr=plt.Unit(),
                        ),
                    )
                )
        self.imports_dataclasses = self.imports_dataclasses or "dataclass" in imported_names
        self.imports_astuple = self.imports_astuple or "astuple" in imported_names
        return additional_assigns

    def visit_Call(self, node: Call) -> Call:
        node = self.generic_visit(node)
        if isinstance(node.func, Name) and node.func.id == "astuple":
            assert (
                self.imports_astuple
            ), "astuple must be imported via 'from dataclasses import astuple'"
        return node

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        assert (
            self.imports_dataclasses
        ), "dataclasses must be imported in order to use datum classes"
        assert (
            len(node.decorator_list) == 1
        ), "Class definitions must have the decorator @dataclass"
        if isinstance(node.decorator_list[0], Call):
            node_decorator = node.decorator_list[0].func
        elif isinstance(node.decorator_list[0], Name):
            node_decorator = node.decorator_list[0]
        else:
            raise AssertionError("Class definitions must have the decorator @dataclass")
        assert isinstance(
            node_decorator, Name
        ), "Class definitions must have the decorator @dataclass"
        assert (
            node_decorator.id == "dataclass"
        ), "Class definitions must have the decorator @dataclass"
        return node
