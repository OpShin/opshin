from ast import *
from typing import Optional

from ..util import CompilingNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportPlutusData(CompilingNodeTransformer):
    step = "Resolving imports and usage of PlutusData and Datum"

    imports_plutus_data = False
    imports_anything = False
    imports_bytestring = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "pycardano":
            return node
        assert (
            len(node.names) <= 2
        ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData' or a subset."
        for imported in node.names:
            if imported.name == "Datum":
                assert (
                    imported.asname == "Anything"
                ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData' or a subset"
                self.imports_anything = True
            elif imported.name == "PlutusData":
                assert (
                    imported.asname == None
                ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData' or a subset"
                self.imports_plutus_data = True
            elif imported.name == "ByteString":
                assert (
                    imported.asname == None
                ), "The program must contain one 'from pycardano import Datum as Anything, PlutusData, ByteString' or a subset"
                self.imports_bytestring = True
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

    def visit_Name(self, node: Name) -> Name:
        if node.id == "Anything":
            assert (
                self.imports_anything
            ), "Datum must be imported as Anything to use it. Add one `from pycardano import Datum as Anything, PlutusData` to the beginning of the file."
        return node
