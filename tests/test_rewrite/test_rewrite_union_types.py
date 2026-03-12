"""
Tests for scripts/rewrite_union_types.py – the pre-commit hook that converts
Python 3.10+ union type syntax into Python 3.9-compatible equivalents.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Make the scripts package importable when running from the repo root.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.rewrite_union_types import (
    _rewrite_annotation,
    _collect_replacements,
    _update_typing_import,
    rewrite_file,
    main,
)
import ast


# ---------------------------------------------------------------------------
# Unit tests for _rewrite_annotation
# ---------------------------------------------------------------------------


def _parse_annotation(src: str) -> ast.expr:
    """Parse a single expression and return its AST node."""
    return ast.parse(src, mode="eval").body


class TestRewriteAnnotation:
    def test_simple_optional(self):
        node = _parse_annotation("int | None")
        assert _rewrite_annotation(node) == "Optional[int]"

    def test_reversed_optional(self):
        node = _parse_annotation("None | int")
        assert _rewrite_annotation(node) == "Optional[int]"

    def test_simple_union(self):
        node = _parse_annotation("int | str")
        assert _rewrite_annotation(node) == "Union[int, str]"

    def test_chained_optional(self):
        node = _parse_annotation("int | str | None")
        assert _rewrite_annotation(node) == "Optional[Union[int, str]]"

    def test_chained_union(self):
        node = _parse_annotation("int | str | bytes")
        assert _rewrite_annotation(node) == "Union[int, str, bytes]"

    def test_nested_in_subscript(self):
        node = _parse_annotation("Dict[str | None, int]")
        assert _rewrite_annotation(node) == "Dict[Optional[str], int]"

    def test_nested_union_in_list(self):
        node = _parse_annotation("List[int | str]")
        assert _rewrite_annotation(node) == "List[Union[int, str]]"

    def test_no_union(self):
        node = _parse_annotation("int")
        assert _rewrite_annotation(node) == "int"

    def test_plain_name_unchanged(self):
        node = _parse_annotation("Optional[int]")
        assert _rewrite_annotation(node) == "Optional[int]"

    def test_multiple_none_operands(self):
        """``None | int | None`` should collapse to ``Optional[int]``."""
        node = _parse_annotation("None | int | None")
        assert _rewrite_annotation(node) == "Optional[int]"


# ---------------------------------------------------------------------------
# Integration tests: rewrite_file
# ---------------------------------------------------------------------------


def _write_temp(content: str) -> Path:
    fd, name = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    Path(name).write_text(content, encoding="utf-8")
    return Path(name)


class TestRewriteFile:
    def _run(self, source: str) -> tuple[bool, str]:
        path = _write_temp(source)
        try:
            changed = rewrite_file(path)
            result = path.read_text(encoding="utf-8")
        finally:
            path.unlink()
        return changed, result

    def test_no_union_untouched(self):
        src = "def foo(x: int) -> str:\n    pass\n"
        changed, result = self._run(src)
        assert not changed
        assert result == src

    def test_simple_param_optional(self):
        src = "def foo(x: int | None) -> str:\n    pass\n"
        changed, result = self._run(src)
        assert changed
        assert "Optional[int]" in result
        assert "from typing import Optional" in result

    def test_return_union(self):
        src = "def foo() -> str | bytes:\n    pass\n"
        changed, result = self._run(src)
        assert changed
        assert "Union[str, bytes]" in result
        assert "from typing import Union" in result

    def test_ann_assign_chained(self):
        src = "x: int | str | None = None\n"
        changed, result = self._run(src)
        assert changed
        assert "Optional[Union[int, str]]" in result

    def test_nested_in_subscript(self):
        src = "from typing import Dict\ndef foo(x: Dict[str | None, int]) -> None:\n    pass\n"
        changed, result = self._run(src)
        assert changed
        assert "Dict[Optional[str], int]" in result
        assert "from typing import Dict, Optional" in result

    def test_existing_typing_import_extended(self):
        src = "from typing import Optional\ndef foo(x: int | str) -> Optional[bytes]:\n    pass\n"
        changed, result = self._run(src)
        assert changed
        assert "from typing import Optional, Union" in result

    def test_already_imported_no_duplicate(self):
        src = "from typing import Optional\ndef foo(x: int | None) -> Optional[str]:\n    pass\n"
        changed, result = self._run(src)
        assert changed
        # Only one typing import line
        assert result.count("from typing import") == 1

    def test_async_function(self):
        src = "async def foo(x: int | None) -> str:\n    pass\n"
        changed, result = self._run(src)
        assert changed
        assert "Optional[int]" in result

    def test_multiple_functions(self):
        src = (
            "def foo(x: int | None) -> None:\n    pass\n"
            "def bar(y: str | bytes) -> None:\n    pass\n"
        )
        changed, result = self._run(src)
        assert changed
        assert "Optional[int]" in result
        assert "Union[str, bytes]" in result

    def test_invalid_syntax_skipped(self):
        src = "def foo(x: int | None\n"  # Missing closing paren – invalid
        path = _write_temp(src)
        try:
            changed = rewrite_file(path)
        finally:
            path.unlink()
        assert not changed  # Invalid Python should be skipped gracefully


# ---------------------------------------------------------------------------
# Tests for _update_typing_import
# ---------------------------------------------------------------------------


class TestUpdateTypingImport:
    def test_add_new_import(self):
        src = "x = 1\n"
        result = _update_typing_import(src, {"Optional"})
        assert "from typing import Optional" in result

    def test_extend_existing_import(self):
        src = "from typing import Dict\nx = 1\n"
        result = _update_typing_import(src, {"Optional"})
        assert "from typing import Dict, Optional" in result
        assert result.count("from typing import") == 1

    def test_no_duplicates(self):
        src = "from typing import Optional\nx = 1\n"
        result = _update_typing_import(src, {"Optional"})
        assert result.count("from typing import") == 1

    def test_empty_needed(self):
        src = "x = 1\n"
        result = _update_typing_import(src, set())
        assert result == src


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class TestMain:
    def test_exit_0_no_changes(self):
        path = _write_temp("def foo(x: int) -> str:\n    pass\n")
        try:
            rc = main([str(path)])
        finally:
            path.unlink()
        assert rc == 0

    def test_exit_1_on_change(self):
        path = _write_temp("def foo(x: int | None) -> str:\n    pass\n")
        try:
            rc = main([str(path)])
        finally:
            path.unlink()
        assert rc == 1

    def test_no_files_exit_0(self):
        assert main([]) == 0
