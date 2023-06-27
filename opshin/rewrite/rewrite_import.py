import ast

import importlib
import importlib.util
import pathlib
import typing
import sys
from ast import *

from ..util import CompilingNodeTransformer

"""
Checks that there was an import of dataclass if there are any class definitions
"""


def import_module(name, package=None):
    """An approximate implementation of import."""
    absolute_name = importlib.util.resolve_name(name, package)
    try:
        return sys.modules[absolute_name]
    except KeyError:
        pass

    path = None
    if "." in absolute_name:
        parent_name, _, child_name = absolute_name.rpartition(".")
        parent_module = import_module(parent_name)
        path = parent_module.__spec__.submodule_search_locations
    for finder in sys.meta_path:
        spec = finder.find_spec(absolute_name, path)
        if spec is not None:
            break
    else:
        msg = f"No module named {absolute_name!r}"
        raise ModuleNotFoundError(msg, name=absolute_name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[absolute_name] = module
    spec.loader.exec_module(module)
    if path is not None:
        setattr(parent_module, child_name, module)
    return module


class RewriteLocation(CompilingNodeTransformer):
    def __init__(self, orig_node):
        self.orig_node = orig_node

    def visit(self, node):
        node = ast.copy_location(node, self.orig_node)
        return super().visit(node)


class RewriteImport(CompilingNodeTransformer):
    step = "Resolving imports"

    def __init__(self, filename=None, package=None):
        self.filename = filename
        self.package = package

    def visit_ImportFrom(
        self, node: ImportFrom
    ) -> typing.Union[ImportFrom, typing.List[AST]]:
        if node.module in [
            "pycardano",
            "typing",
            "dataclasses",
            "hashlib",
            "opshin.bridge",
        ]:
            return node
        assert (
            len(node.names) == 1
        ), "The import must have the form 'from <pkg> import *'"
        assert (
            node.names[0].name == "*"
        ), "The import must have the form 'from <pkg> import *'"
        assert (
            node.names[0].asname == None
        ), "The import must have the form 'from <pkg> import *'"
        # TODO set anchor point according to own package
        if self.filename:
            sys.path.append(str(pathlib.Path(self.filename).parent.absolute()))
        module = import_module(node.module, self.package)
        if self.filename:
            sys.path.pop()
        module_file = pathlib.Path(module.__file__)
        assert (
            module_file.suffix == ".py"
        ), "The import must import a single python file."
        # visit the imported file again - make sure that recursive imports are resolved accordingly
        with module_file.open("r") as fp:
            module_content = fp.read()
        resolved = parse(module_content, filename=module_file.name)
        # annotate this to point to the original line number!
        RewriteLocation(node).visit(resolved)
        # recursively import all statements there
        recursively_resolved: Module = RewriteImport(
            filename=str(module_file), package=module.__package__
        ).visit(resolved)
        return recursively_resolved.body
