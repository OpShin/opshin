from ast import *
from copy import copy

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteDataclasses(NodeTransformer):

    imports_dataclass = False

    def visit_ImportFrom(self, node: ImportFrom) -> None:
        assert (
            node.module == "dataclasses"
        ), "The program must contain one 'from dataclasses import dataclass'"
        assert (
            len(node.names) == 1
        ), "The program must contain one 'from dataclasses import dataclass'"
        assert (
            node.names[0].name == "dataclass"
        ), "The program must contain one 'from dataclasses import dataclass'"
        assert (
            node.names[0].asname == None
        ), "The program must contain one 'from dataclasses import dataclass'"
        self.imports_dataclass = True
        return None

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        assert (
            self.imports_dataclass
        ), "The program must contain one 'from dataclasses import dataclass' if classes are defined"
        assert (
            len(node.decorator_list) == 1
        ), "Class definitions must have the decorator @dataclass(frozen=True)"
        assert isinstance(
            node.decorator_list[0], Call
        ), "Class definitions must have the decorator @dataclass(frozen=True)"
        assert isinstance(
            node.decorator_list[0].func, Name
        ), "Class definitions must have the decorator @dataclass(frozen=True)"
        assert (
            node.decorator_list[0].func.id == "dataclass"
        ), "Class definitions must have the decorator @dataclass(frozen=True)"
        return node
