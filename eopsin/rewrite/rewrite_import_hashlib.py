from ast import *
from typing import Optional

from ..util import CompilingNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportHashlib(CompilingNodeTransformer):
    step = "Resolving imports and usage of hashlib"

    imports_hashlib = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "hashlib":
            return node
        assert (
            len(node.names) == 3
        ), "The program must contain one 'from hashlib import sha256, sha3_256, blake2b'"
        for i, n in enumerate(["sha256", "sha3_256", "blake2b"]):
            assert (
                node.names[i].name == n
            ), "The program must contain one 'from hashlib import sha256, sha3_256, blake2b'"
            assert (
                node.names[i].asname == None
            ), "The program must contain one 'from hashlib import sha256, sha3_256, blake2b'"
        self.imports_hashlib = True
        return None

    def visit_Name(self, node: Name) -> Name:
        if not node.id in ["sha256", "sha3_256", "blake2b"]:
            return node
        assert (
            self.imports_hashlib
        ), f"hashlib must be imported in order to use {node.id}"
        return node
