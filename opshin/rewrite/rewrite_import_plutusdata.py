from ast import *
from typing import Optional

from ..util import CompilingNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportPlutusData(CompilingNodeTransformer):
    step = "Resolving imports and usage of PlutusData and Datum"

    imports_plutus_data = False

    def _is_contract_class(self, node: ClassDef) -> bool:
        if any(isinstance(base, Name) and base.id == "Contract" for base in node.bases):
            return True
        return node.name == "Contract" and not node.decorator_list and not node.bases

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
        if self._is_contract_class(node):
            return node
        assert (
            len(node.decorator_list) == 1
        ), f"Class definitions must have no decorators but @dataclass, {node.name} has {tuple(node.decorator_list)}"
        assert (
            len(node.bases) == 1
        ), f"Class definitions must inherit exactly from PlutusData (i.e., `class {node.name}(PlutusData)`), {node.name} inherits from {tuple(node.bases)}"
        assert isinstance(
            node.bases[0], Name
        ), f"The inheritance must be direct, using the name PlutusData (i.e., `class {node.name}(PlutusData)`), {node.name} uses {node.bases}"
        base: Name = node.bases[0]
        assert (
            base.id == "PlutusData"
        ), f"Class definitions must inherit from PlutusData, {node.name} uses {base}"
        assert (
            self.imports_plutus_data
        ), "PlutusData must be imported in order to use datum classes"
        return node
