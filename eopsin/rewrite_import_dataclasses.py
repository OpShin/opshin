from ast import *
from copy import copy
from typing import Optional

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportDataclasses(NodeTransformer):

    imports_dataclasses = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "dataclasses":
            return node
        assert (
            len(node.names) == 1
        ), "The program must contain one 'from dataclasses import dataclass'"
        for i, n in enumerate(["dataclass"]):
            assert (
                node.names[i].name == n
            ), "The program must contain one 'from dataclasses import dataclass'"
            assert (
                node.names[i].asname == None
            ), "The program must contain one 'from dataclasses import dataclass'"
        self.imports_dataclasses = True
        return None

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        assert (
            self.imports_dataclasses
        ), "dataclasses must be imported in order to use datum classes"
        assert (
            len(node.decorator_list) == 1
        ), "Class definitions must have no decorators but @dataclass()"
        assert isinstance(
            node.decorator_list[0], Call
        ), "Class definitions must have no decorators but @dataclass()"
        assert isinstance(
            node.decorator_list[0].func, Name
        ), "Class definitions must have no decorators but @dataclass()"
        assert (
            node.decorator_list[0].func.id == "dataclass"
        ), "Class definitions must have no decorators but @dataclass()"
        return node
