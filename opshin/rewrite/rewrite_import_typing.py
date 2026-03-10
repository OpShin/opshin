from ast import *
from typing import Optional

from ..util import CompilingNodeTransformer, transform_annotation

"""
Checks that there was an import of dataclass if there are any class definitions
"""


ALLOWED_TYPING_IMPORTS = {"Dict", "List", "Union", "Self"}


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

    def mark_typing_annotation_usage(self, annotation: expr, class_name: str):
        def mark(node: expr):
            if isinstance(node, Name):
                if node.id in ALLOWED_TYPING_IMPORTS and node.id not in self.imports:
                    raise ValueError(
                        f"{node.id} used, which is a keyword for special OpShin types, but typing not imported. Please add 'from typing import {node.id}'"
                    )
                if node.id == "Self":
                    node.idSelf = class_name
            return node

        return transform_annotation(annotation, mark)

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        for i, attribute in enumerate(node.body):
            if isinstance(attribute, FunctionDef):
                for j, arg in enumerate(attribute.args.args):
                    node.body[i].args.args[j].annotation = (
                        self.mark_typing_annotation_usage(arg.annotation, node.name)
                    )
                node.body[i].returns = self.mark_typing_annotation_usage(
                    attribute.returns, node.name
                )

        return node
