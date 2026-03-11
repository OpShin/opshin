from ast import *
from typing import Optional

from ..util import CompilingNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportDataclasses(CompilingNodeTransformer):
    step = "Resolving the import and usage of dataclass"

    def __init__(self):
        self.imports_dataclasses = False
        self.imports_astuple = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "dataclasses":
            return node
        imported_names = {name.name for name in node.names}
        assert "dataclass" in imported_names, (
            "The program must contain 'from dataclasses import dataclass'"
        )
        for imported_name in node.names:
            assert (
                imported_name.asname == None
            ), "Imports from dataclasses cannot be aliased"
            assert imported_name.name in {"dataclass", "astuple"}, (
                "Only 'dataclass' and 'astuple' may be imported from dataclasses"
            )
        self.imports_dataclasses = True
        self.imports_astuple = self.imports_astuple or "astuple" in imported_names
        return None

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
