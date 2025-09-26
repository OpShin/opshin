import ast

import importlib
import importlib.util
import pathlib
import typing
import sys
from ast import *
from copy import copy
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
        self.selective_imports = {}  # Track which names were selectively imported
        self.current_module = None  # Track current module being processed

    def visit_Module(self, node):
        self.current_module = node
        result = self.generic_visit(node)
        # Store selective imports info in the module for later steps
        result.selective_imports = self.selective_imports
        return result

    def visit_Import(self, node):
        error_msg = f"The import must have the form 'from <pkg> import *' or 'from <pkg> import name1, name2, ...' or import from one of the special modules {', '.join(SPECIAL_IMPORTS)}"
        raise SyntaxError(error_msg)

    def visit_ImportFrom(
        self, node: ImportFrom
    ) -> typing.Union[ImportFrom, typing.List[AST], None]:
        if node.module in SPECIAL_IMPORTS:
            return node
        error_msg = f"The import must have the form 'from <pkg> import *' or 'from <pkg> import name1, name2, ...' or import from one of the special modules {', '.join(SPECIAL_IMPORTS)}"

        # Handle star imports (existing behavior)
        if len(node.names) == 1 and node.names[0].name == "*":
            assert node.names[0].asname == None, error_msg
            imported_names = None  # Import everything
        else:
            # Handle selective imports: from x import y, z
            imported_names = []
            for alias in node.names:
                assert alias.asname == None, "Import aliases are not supported"
                imported_names.append(alias.name)
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

        # Store the imported names for later use by type inference
        if imported_names is not None:
            self.selective_imports[node.module] = imported_names
            # Store selective import information in the recursive resolver so it propagates
            recursive_resolver.selective_imports.update(self.selective_imports)

            # Apply selective import filtering to the body
            filtered_body = self._apply_selective_import_namespacing(
                recursively_resolved.body, imported_names, node.module
            )
            return filtered_body

        return recursively_resolved.body

    def _apply_selective_import_namespacing(self, body, imported_names, module_name):
        """
        Apply selective import filtering by creating module namespaces.
        Imported names stay as-is, non-imported names get a module prefix.
        """
        filtered_body = []
        imported_names_set = set(imported_names)
        module_prefix = module_name.replace(".", "_")

        class NameRewriter(CompilingNodeTransformer):
            def visit_Name(self, node):
                # Only rewrite names that reference non-imported functions/variables
                if (
                    isinstance(node.ctx, Load)
                    and node.id not in imported_names_set
                    and not node.id.startswith(
                        "_"
                    )  # Don't rewrite already private names
                    and node.id not in ["True", "False", "None"]
                ):  # Don't rewrite constants
                    # Check if this name exists in the current module's definitions
                    for stmt in body:
                        if isinstance(stmt, FunctionDef) and stmt.name == node.id:
                            node.id = f"{module_prefix}_{node.id}"
                            break
                        elif isinstance(stmt, ClassDef) and stmt.name == node.id:
                            node.id = f"{module_prefix}_{node.id}"
                            break
                return node

        rewriter = NameRewriter()

        for stmt in body:
            # Always include import statements
            if isinstance(stmt, (ImportFrom, Import)):
                filtered_body.append(stmt)
                continue

            # Handle function definitions
            if isinstance(stmt, FunctionDef):
                stmt_copy = copy(stmt)
                if stmt.name not in imported_names_set:
                    # Rename non-imported functions with module prefix
                    stmt_copy.name = f"{module_prefix}_{stmt.name}"
                # Rewrite any references inside the function body
                stmt_copy = rewriter.visit(stmt_copy)
                filtered_body.append(stmt_copy)

            # Handle class definitions
            elif isinstance(stmt, ClassDef):
                stmt_copy = copy(stmt)
                if stmt.name not in imported_names_set:
                    # Rename non-imported classes with module prefix
                    stmt_copy.name = f"{module_prefix}_{stmt.name}"
                # Rewrite any references inside the class body
                stmt_copy = rewriter.visit(stmt_copy)
                filtered_body.append(stmt_copy)

            # Handle variable assignments - only include explicitly imported ones
            elif isinstance(stmt, (Assign, AnnAssign)):
                should_include = False
                if isinstance(stmt, Assign):
                    for target in stmt.targets:
                        if isinstance(target, Name) and target.id in imported_names_set:
                            should_include = True
                            break
                elif isinstance(stmt, AnnAssign):
                    if (
                        isinstance(stmt.target, Name)
                        and stmt.target.id in imported_names_set
                    ):
                        should_include = True

                if should_include:
                    filtered_body.append(stmt)

            else:
                # Include other statements
                filtered_body.append(stmt)

        return filtered_body
