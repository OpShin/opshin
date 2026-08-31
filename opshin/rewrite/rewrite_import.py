import ast

import importlib.machinery
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


def find_module_spec(name, package=None, search_paths=None):
    """Find a Python module without importing or executing it."""
    absolute_name = importlib.util.resolve_name(name, package)
    parts = absolute_name.split(".")
    path = search_paths
    spec = None
    for i in range(len(parts)):
        qualified_name = ".".join(parts[: i + 1])
        spec = importlib.machinery.PathFinder.find_spec(qualified_name, path)
        if spec is None:
            raise ModuleNotFoundError(
                f"No module named {absolute_name!r}", name=absolute_name
            )
        if i != len(parts) - 1:
            path = spec.submodule_search_locations
            if path is None:
                raise ModuleNotFoundError(
                    f"No module named {absolute_name!r}; {qualified_name!r} is not a package",
                    name=absolute_name,
                )
    return spec


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
    "opshin.std.bls12_381",
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
        import_name = "." * node.level + (node.module or "")
        search_paths = list(sys.path)
        if self.filename:
            search_paths.insert(0, str(pathlib.Path(self.filename).parent.absolute()))
        spec = find_module_spec(import_name, self.package, search_paths)
        if spec.origin is None:
            raise ImportError(f"Module {spec.name!r} has no Python source file")
        module_file = pathlib.Path(spec.origin)
        if module_file.suffix == ".pyc":
            module_file = module_file.with_suffix(".py")
        module_file = module_file.resolve()
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
            package=(
                spec.name
                if spec.submodule_search_locations is not None
                else spec.name.rpartition(".")[0]
            ),
            resolved_imports=self.resolved_imports,
        )
        recursively_resolved: Module = recursive_resolver.visit(resolved)
        self.resolved_imports.update(recursive_resolver.resolved_imports)
        return recursively_resolved.body
