import pathlib
from ast import parse
import importlib

from ast import *
from copy import copy
from typing import Union

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImport(NodeTransformer):

    imports_plutus_data = False

    def visit_ImportFrom(self, node: ImportFrom) -> Union[ImportFrom, AST]:
        if node.module in ["pycardano", "typing"]:
            return node
        assert (
            len(node.names) == 1
        ), "The import must have the form 'from <pkg> import *'"
        assert (
            node.names[0].name == "*"
        ), "The import must have the form 'from <pkg> import *'"
        assert (
            node.names[0].asname == None
        ), "The import must have the form 'from <pkg> import *'"
        # TODO set anchor point according to own package
        module_file = pathlib.Path(importlib.import_module(node.module).__file__)
        assert (
            module_file.suffix == "py"
        ), "The import must import a single python file."
        # visit the imported file again - make sure that recursive imports are resolved accordingly
        return self.visit(parse(module_file))

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        assert (
            len(node.decorator_list) == 0
        ), "Class definitions must have no decorators"
        assert (
            len(node.bases) == 0
        ), "Class definitions must inherit only from PlutusData"
        assert (
            isinstance(node.bases[0], Name),
        ), "The inheritance must be direct, using the name PlutusData"
        base: Name = node.bases[0]
        assert base.id == "PlutusData", "Class definitions must inherit from PlutusData"
        assert (
            self.imports_plutus_data
        ), "PlutusData must be imported in order to use datum classes"
        return node
