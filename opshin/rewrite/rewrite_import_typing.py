from ast import *
from typing import Optional

from ..util import CompilingNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportTyping(CompilingNodeTransformer):
    step = "Checking import and usage of typing"

    imports_typing = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "typing":
            return node
        assert (
            len(node.names) == 3
        ), "The program must contain one 'from typing import Dict, List, Union'"
        for i, n in enumerate(["Dict", "List", "Union"]):
            assert (
                node.names[i].name == n
            ), "The program must contain one 'from typing import Dict, List, Union'"
            assert (
                node.names[i].asname == None
            ), "The program must contain one 'from typing import Dict, List, Union'"
        self.imports_typing = True
        return None

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        assert (
            self.imports_typing
        ), "typing must be imported in order to use datum classes"
        return node
