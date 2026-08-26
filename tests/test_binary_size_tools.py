import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, path: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


CHECK_BINARY_SIZES = load_module(
    "check_binary_sizes", str(REPO_ROOT / "scripts" / "check_binary_sizes.py")
)
BINARY_SIZE_TRACKER = load_module(
    "binary_size_tracker", str(REPO_ROOT / "scripts" / "binary_size_tracker.py")
)


class BinarySizeToolTests(unittest.TestCase):
    def test_compile_contract_returns_none_on_failure(self):
        with patch.object(
            BINARY_SIZE_TRACKER,
            "run_command",
            return_value=(1, "", "boom"),
        ):
            size = BINARY_SIZE_TRACKER.compile_contract(
                "examples/smart_contracts/assert_sum.py",
                "O1",
                work_dir=str(REPO_ROOT),
            )
        self.assertIsNone(size)

    def test_fallback_config_uses_current_contracts(self):
        config = BINARY_SIZE_TRACKER.load_config("/definitely/missing/config.yaml")
        contract_names = {contract["name"] for contract in config["contracts"]}
        self.assertIn("wrapped_token", contract_names)
        self.assertNotIn("dual_use", contract_names)

    def test_run_tracker_comparison_propagates_failure(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as baseline_file:
            completed_process = Mock(returncode=7)
            with patch.object(
                CHECK_BINARY_SIZES.subprocess,
                "run",
                return_value=completed_process,
            ) as run_mock:
                return_code = CHECK_BINARY_SIZES.run_tracker_comparison(
                    Path("/tmp/binary_size_tracker.py"),
                    baseline_file.name,
                )
        self.assertEqual(return_code, 7)
        run_mock.assert_called_once()
