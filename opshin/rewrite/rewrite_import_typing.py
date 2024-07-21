from ast import *
from typing import Optional

from ..util import CompilingNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


class RewriteImportTyping(CompilingNodeTransformer):
    step = "Checking import and usage of typing"

    imports_typing = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.imports_Self = False

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "typing":
            return node
        if len(node.names) == 1 and node.names[0].name == "Self":
            self.imports_Self = True
            return None
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
        if self.imports_Self:
            for i, attribute in enumerate(node.body):
                if isinstance(attribute, FunctionDef):
                    for j, arg in enumerate(attribute.args.args):
                        if (
                            isinstance(arg.annotation, Name)
                            and arg.annotation.id == "Self"
                        ):
                            node.body[i].args.args[j].annotation.idSelf = node.name
                    if (
                        isinstance(attribute.returns, Name)
                        and attribute.returns.id == "Self"
                    ):
                        node.body[i].returns.idSelf = node.name

        return node
