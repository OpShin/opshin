from ast import *
from copy import copy
from typing import Optional

from ..util import CompilingNodeTransformer, AnnotationNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


ALLOWED_TYPING_IMPORTS = {"Dict", "List", "Union", "Self"}


class TypingAnnotationMarker(AnnotationNodeTransformer):
    def __init__(self, imports, class_name: str):
        self.imports = imports
        self.class_name = class_name

    def visit_Name(self, node: Name):
        node_cp = copy(node)
        if node_cp.id in ALLOWED_TYPING_IMPORTS and node_cp.id not in self.imports:
            raise ValueError(
                f"{node_cp.id} used, which is a keyword for special OpShin types, but typing not imported. Please add 'from typing import {node_cp.id}'"
            )
        if node_cp.id == "Self":
            node_cp.idSelf = self.class_name
        return node_cp


class RewriteImportTyping(CompilingNodeTransformer):
    step = "Checking import and usage of typing"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.imports = set()

    def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
        if node.module != "typing":
            return node

        for n in node.names:
            if n.name not in ALLOWED_TYPING_IMPORTS:
                raise ValueError(
                    f"Only the following imports from typing are allowed: {ALLOWED_TYPING_IMPORTS}, found {n.name}"
                )
            if n.asname is not None:
                raise ValueError("Imports from typing cannot be aliased")
            self.imports.add(n.name)
        return None

    def visit_Name(self, node: Name) -> Optional[Name]:
        if node.id in ALLOWED_TYPING_IMPORTS and node.id not in self.imports:
            raise ValueError(
                f"{node.id} used, which is a keyword for special OpShin types, but typing not imported. Please add 'from typing import {node.id}'"
            )
        return node

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        for i, attribute in enumerate(node.body):
            if isinstance(attribute, FunctionDef):
                for j, arg in enumerate(attribute.args.args):
                    node.body[i].args.args[j].annotation = TypingAnnotationMarker(
                        self.imports, node.name
                    ).visit(arg.annotation)
                node.body[i].returns = TypingAnnotationMarker(
                    self.imports, node.name
                ).visit(attribute.returns)

        return node
