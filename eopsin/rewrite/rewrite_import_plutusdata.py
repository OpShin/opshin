from ast import *
from typing import Optional

from ..util import CompilingNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportPlutusData(CompilingNodeTransformer):
    step = "Resolving imports and usage of PlutusData and Datum"

    imports_plutus_data = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "pycardano":
            return node
        assert (
            len(node.names) == 2
        ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData'"
        assert (
            node.names[0].name == "Datum"
        ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData'"
        assert (
            node.names[0].asname == "Anything"
        ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData'"
        assert (
            node.names[1].name == "PlutusData"
        ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData'"
        assert (
            node.names[1].asname == None
        ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData'"
        self.imports_plutus_data = True
        return None

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        assert (
            len(node.decorator_list) == 1
        ), "Class definitions must have no decorators but @dataclass"
        assert (
            len(node.bases) == 1
        ), "Class definitions must inherit only from PlutusData"
        assert isinstance(
            node.bases[0], Name
        ), "The inheritance must be direct, using the name PlutusData"
        base: Name = node.bases[0]
        assert base.id == "PlutusData", "Class definitions must inherit from PlutusData"
        assert (
            self.imports_plutus_data
        ), "PlutusData must be imported in order to use datum classes"
        return node
