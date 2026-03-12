#!/usr/bin/env python3
"""
Pre-commit hook that rewrites Python 3.10+ union type syntax to Python 3.9
compatible syntax.

Converts:
  - ``x | None``      -> ``Optional[x]``
  - ``None | x``      -> ``Optional[x]``
  - ``x | y``         -> ``Union[x, y]``
  - ``x | y | None``  -> ``Optional[Union[x, y]]``

Adds required ``from typing import Optional, Union`` imports as needed.

Exit codes:
  0 – no changes were necessary
  1 – at least one file was rewritten (commit will be rejected so the user
      can ``git add`` the updated files and re-commit)
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Annotation AST helpers
# ---------------------------------------------------------------------------


def _collect_bitor_operands(node: ast.expr) -> list[ast.expr]:
    """Flatten a chain of BitOr BinOp nodes into a flat list of operands."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _collect_bitor_operands(node.left) + _collect_bitor_operands(
            node.right
        )
    return [node]


def _has_bitor(node: ast.AST) -> bool:
    """Return True if *node* contains at least one BitOr BinOp."""
    return any(
        isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr)
        for n in ast.walk(node)
    )


def _is_none_constant(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _rewrite_annotation(node: ast.expr) -> str:
    """Return a Python 3.9-compatible string for *node* (an annotation AST).

    Recursively rewrites any ``x | y`` sub-expression into ``Union[x, y]``
    or ``Optional[x]`` (when one of the operands is ``None``).

    For non-union nodes the output of ``ast.unparse`` is returned unchanged.
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        operands = _collect_bitor_operands(node)
        none_count = sum(1 for t in operands if _is_none_constant(t))
        non_none = [t for t in operands if not _is_none_constant(t)]
        non_none_strs = [_rewrite_annotation(t) for t in non_none]

        if none_count:
            if len(non_none_strs) == 1:
                return f"Optional[{non_none_strs[0]}]"
            else:
                return f"Optional[Union[{', '.join(non_none_strs)}]]"
        else:
            return f"Union[{', '.join(non_none_strs)}]"

    if isinstance(node, ast.Subscript):
        value_str = _rewrite_annotation(node.value)
        slice_str = _rewrite_annotation(node.slice)
        return f"{value_str}[{slice_str}]"

    if isinstance(node, ast.Tuple):
        # Appears as the slice of multi-arg generics, e.g. Dict[str, int]
        return ", ".join(_rewrite_annotation(elt) for elt in node.elts)

    return ast.unparse(node)


# ---------------------------------------------------------------------------
# Source-level rewriting
# ---------------------------------------------------------------------------


def _replace_in_source(
    lines: list[str],
    replacements: list[tuple[int, int, int, int, str]],
) -> list[str]:
    """Apply *replacements* to *lines* (1-indexed line numbers).

    Each replacement is ``(lineno, col_offset, end_lineno, end_col_offset,
    new_text)``.  Replacements are applied bottom-to-top so that earlier
    positions remain valid after each substitution.
    """
    for lineno, col, end_lineno, end_col, new_text in sorted(
        replacements, key=lambda r: (r[0], r[1]), reverse=True
    ):
        if lineno == end_lineno:
            line = lines[lineno - 1]
            lines[lineno - 1] = line[:col] + new_text + line[end_col:]
        else:
            # Multi-line annotation (very rare)
            first = lines[lineno - 1][:col] + new_text
            rest = lines[end_lineno - 1][end_col:]
            lines[lineno - 1 : end_lineno] = [first + rest]
    return lines


def _annotation_replacement(
    ann: ast.expr,
) -> Optional[tuple[int, int, int, int, str]]:
    """Return a replacement tuple for *ann* if it contains BitOr, else None."""
    if not _has_bitor(ann):
        return None
    new_text = _rewrite_annotation(ann)
    return (ann.lineno, ann.col_offset, ann.end_lineno, ann.end_col_offset, new_text)


def _collect_replacements(tree: ast.Module) -> list[tuple[int, int, int, int, str]]:
    """Walk *tree* and collect all annotation replacements needed."""
    replacements: list[tuple[int, int, int, int, str]] = []

    def _process(ann: Optional[ast.expr]) -> None:
        if ann is None:
            return
        r = _annotation_replacement(ann)
        if r is not None:
            replacements.append(r)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in (
                node.args.posonlyargs
                + node.args.args
                + node.args.kwonlyargs
                + ([node.args.vararg] if node.args.vararg else [])
                + ([node.args.kwarg] if node.args.kwarg else [])
            ):
                _process(arg.annotation)
            _process(node.returns)
        elif isinstance(node, ast.AnnAssign):
            _process(node.annotation)

    return replacements


# ---------------------------------------------------------------------------
# Import management
# ---------------------------------------------------------------------------

_TYPING_NAMES = {"Optional", "Union"}


def _needed_typing_imports(replacements: list[tuple[int, int, int, int, str]]) -> set[str]:
    """Return the set of typing names introduced by *replacements*."""
    needed: set[str] = set()
    for *_, new_text in replacements:
        for name in _TYPING_NAMES:
            if name in new_text:
                needed.add(name)
    return needed


def _update_typing_import(source: str, needed: set[str]) -> str:
    """Ensure *source* imports every name in *needed* from ``typing``.

    Behaviour:
    * If there is already a ``from typing import ...`` statement, the missing
      names are appended to it (sorted).
    * If there is none, a new ``from typing import ...`` line is prepended.
    """
    if not needed:
        return source

    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)

    # Find existing ``from typing import`` nodes
    existing_node: Optional[ast.ImportFrom] = None
    existing_line: Optional[int] = None  # 0-indexed
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "typing":
            existing_node = node
            existing_line = node.lineno - 1
            break

    if existing_node is not None:
        # Work out which names are already imported
        already = {alias.name for alias in existing_node.names}
        to_add = needed - already
        if not to_add:
            return source
        all_names = sorted(already | to_add)
        # Rebuild the import line preserving indentation
        indent = len(lines[existing_line]) - len(lines[existing_line].lstrip())
        new_import = (
            " " * indent + "from typing import " + ", ".join(all_names) + "\n"
        )
        lines[existing_line] = new_import
        return "".join(lines)

    # No existing typing import – prepend one before any non-future imports
    new_import_line = "from typing import " + ", ".join(sorted(needed)) + "\n"
    # Find a good insertion point: after module docstring / __future__ imports
    insert_at = 0
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            # Module-level docstring
            insert_at = node.end_lineno
        elif isinstance(node, ast.ImportFrom) and node.module == "__future__":
            insert_at = node.end_lineno
        else:
            break

    lines.insert(insert_at, new_import_line)
    return "".join(lines)


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------


def rewrite_file(path: Path) -> bool:
    """Rewrite *path* in-place.  Returns True if the file was modified."""
    source = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False  # Not valid Python – leave untouched

    replacements = _collect_replacements(tree)
    if not replacements:
        return False

    lines = source.splitlines(keepends=True)
    # splitlines(keepends=True) preserves trailing newline presence correctly
    new_lines = _replace_in_source(list(lines), replacements)
    new_source = "".join(new_lines)

    # Update / add typing imports
    needed = _needed_typing_imports(replacements)
    new_source = _update_typing_import(new_source, needed)

    if new_source == source:
        return False

    path.write_text(new_source, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rewrite Python 3.10+ union type annotations to Python 3.9 syntax."
    )
    parser.add_argument("files", nargs="*", help="Python files to process")
    args = parser.parse_args(argv)

    changed = False
    for filename in args.files:
        path = Path(filename)
        if rewrite_file(path):
            print(f"Rewrote {path}")
            changed = True

    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
