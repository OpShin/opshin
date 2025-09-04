import ast

import importlib
import importlib.util
import pathlib
import typing
import sys
from ast import *
from ordered_set import OrderedSet

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
    spec = None
    error_msg = None
    try:
        if "." in absolute_name:
            parent_name, _, child_name = absolute_name.rpartition(".")
            parent_module = import_module(parent_name)
            path = parent_module.__spec__.submodule_search_locations
        for finder in sys.meta_path:
            spec = finder.find_spec(absolute_name, path)
            if spec is not None:
                break
    except (ImportError, AttributeError) as e:
        error_msg = str(e)
    if spec is None:
        msg = f"No module named {absolute_name!r}"
        if error_msg:
            msg += f"; {error_msg}"
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


SPECIAL_IMPORTS = [
    "pycardano",
    "typing",
    "dataclasses",
    "hashlib",
    "opshin.bridge",
    "opshin.std.integrity",
]


class RewriteImport(CompilingNodeTransformer):
    step = "Resolving imports"

    def __init__(self, filename=None, package=None, resolved_imports=None):
        self.filename = filename
        self.package = package
        self.resolved_imports = resolved_imports or OrderedSet()

    def visit_Import(self, node):
        error_msg = f"The import must have the form 'from <pkg> import *' or import from one of the special modules {', '.join(SPECIAL_IMPORTS)}"
        raise SyntaxError(error_msg)

    def visit_ImportFrom(
        self, node: ImportFrom
    ) -> typing.Union[ImportFrom, typing.List[AST], None]:
        if node.module in SPECIAL_IMPORTS:
            return node
        error_msg = f"The import must have the form 'from <pkg> import *' or import from one of the special modules {', '.join(SPECIAL_IMPORTS)}"
        assert len(node.names) == 1, error_msg
        assert node.names[0].name == "*", error_msg
        assert node.names[0].asname == None, error_msg
        # TODO set anchor point according to own package
        if self.filename:
            sys.path.append(str(pathlib.Path(self.filename).parent.absolute()))
        module = import_module(node.module, self.package)
        if self.filename:
            sys.path.pop()
        module_file = pathlib.Path(module.__file__)
        if module_file.suffix == ".pyc":
            module_file = module_file.with_suffix(".py")
        if module_file in self.resolved_imports:
            # Import was already resolved and its names are visible
            return None
        self.resolved_imports.add(module_file)
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
        recursive_resolver = RewriteImport(
            filename=str(module_file),
            package=module.__package__,
            resolved_imports=self.resolved_imports,
        )
        recursively_resolved: Module = recursive_resolver.visit(resolved)
        self.resolved_imports.update(recursive_resolver.resolved_imports)
        return recursively_resolved.body
