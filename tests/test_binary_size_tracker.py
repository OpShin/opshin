import importlib.util
import sys
from pathlib import Path

import pytest

TRACKER_PATH = Path(__file__).parents[1] / "scripts" / "binary_size_tracker.py"
SPEC = importlib.util.spec_from_file_location("binary_size_tracker", TRACKER_PATH)
assert SPEC is not None
assert SPEC.loader is not None
binary_size_tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(binary_size_tracker)


def test_size_changes_have_a_dedicated_exit_code(monkeypatch):
    monkeypatch.setattr(binary_size_tracker, "compare_with_baseline", lambda *_: True)
    monkeypatch.setattr(sys, "argv", [str(TRACKER_PATH), "compare"])

    with pytest.raises(SystemExit) as exc_info:
        binary_size_tracker.main()

    assert exc_info.value.code == binary_size_tracker.SIZE_CHANGES_EXIT_CODE


def test_checker_crashes_are_not_reclassified_as_size_changes(monkeypatch):
    def crash(*_):
        raise RuntimeError("compiler crashed")

    monkeypatch.setattr(binary_size_tracker, "compare_with_baseline", crash)
    monkeypatch.setattr(sys, "argv", [str(TRACKER_PATH), "compare"])

    with pytest.raises(RuntimeError, match="compiler crashed"):
        binary_size_tracker.main()
