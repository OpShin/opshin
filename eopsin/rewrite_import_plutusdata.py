from ast import *
from copy import copy
from typing import Optional

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportPlutusData(NodeTransformer):

    imports_plutus_data = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "pycardano":
            return node
        assert (
            len(node.names) == 2
        ), "The program must contain one 'from pycardano import Datum, PlutusData'"
        assert (
            node.names[0].name == "Datum"
        ), "The program must contain one 'from pycardano import Datum, PlutusData'"
        assert (
            node.names[0].asname == None
        ), "The program must contain one 'from pycardano import Datum, PlutusData'"
        assert (
            node.names[1].name == "PlutusData"
        ), "The program must contain one 'from pycardano import Datum, PlutusData'"
        assert (
            node.names[1].asname == None
        ), "The program must contain one 'from pycardano import Datum, PlutusData'"
        self.imports_plutus_data = True
        return None

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
