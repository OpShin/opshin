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

    def visit_Name(self, node: Name) -> Optional[Name]:
        if node.id == "Self" and not self.imports_Self:
            raise ValueError("Self used but not imported from typing")
        if node.id in {"Dict", "List", "Union"} and not self.imports_typing:
            raise ValueError(
                f"{node.id} used but typing not imported. Please add 'from typing import Dict, List, Union'"
            )
        return node

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        assert (
            self.imports_typing
        ), "typing must be imported in order to use datum classes"
        for i, attribute in enumerate(node.body):
            if isinstance(attribute, FunctionDef):
                for j, arg in enumerate(attribute.args.args):
                    if isinstance(arg.annotation, Name) and arg.annotation.id == "Self":
                        assert (
                            self.imports_Self
                        ), "Self used but not imported from typing. Please add 'from typing import Self'"
                        node.body[i].args.args[j].annotation.idSelf = node.name
                    if (
                        isinstance(arg.annotation, Subscript)
                        and arg.annotation.value.id == "Union"
                    ):
                        for k, s in enumerate(arg.annotation.slice.elts):
                            if isinstance(s, Name) and s.id == "Self":
                                assert (
                                    self.imports_Self
                                ), "Self used but not imported from typing. Please add 'from typing import Self'"
                                node.body[i].args.args[j].annotation.slice.elts[
                                    k
                                ].idSelf = node.name

                if (
                    isinstance(attribute.returns, Name)
                    and attribute.returns.id == "Self"
                ):
                    assert (
                        self.imports_Self
                    ), "Self used but not imported from typing. Please add 'from typing import Self'"
                    node.body[i].returns.idSelf = node.name

        return node
