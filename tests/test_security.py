import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from opshin import builder, CompilerError
from opshin.optimize.optimize_const_folding import OptimizeConstantFolding
from opshin.rewrite.rewrite_import import RewriteImport
from opshin.type_inference import INITIAL_SCOPE

REPOSITORY_ROOT = Path(__file__).parent.parent


@pytest.mark.parametrize("command", ["parse", "compile", "eval_uplc", "lint"])
def test_cli_does_not_execute_contract_source(tmp_path, command):
    marker = tmp_path / "contract-executed"
    contract = tmp_path / "contract.py"
    contract.write_text(f"""\
from opshin.prelude import *

open({str(marker)!r}, "w").write("executed")

def validator(context: ScriptContext) -> None:
    pass
""")

    subprocess.run(
        [sys.executable, "-m", "opshin", command, str(contract)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert not marker.exists()


def test_constant_folding_does_not_execute_unsafe_builtin(tmp_path):
    marker = tmp_path / "constant-folding-executed"
    source = f"""\
open({str(marker)!r}, "w").write("executed")

def validator(_: None) -> None:
    pass
"""

    OptimizeConstantFolding().visit(ast.parse(source))

    assert not marker.exists()


def test_integrity_import_alias_does_not_leak_between_compilations():
    alias = "leaked_integrity_check_security_test"
    imported_source = f"""\
from opshin.prelude import *
from opshin.std.integrity import check_integrity as {alias}

@dataclass()
class Box(PlutusData):
    CONSTR_ID = 0
    value: int

def validator(box: Box) -> None:
    {alias}(box)
"""
    unimported_source = imported_source.replace(
        f"from opshin.std.integrity import check_integrity as {alias}\n", ""
    )

    INITIAL_SCOPE.pop(alias, None)
    try:
        builder._compile(imported_source)
        with pytest.raises(CompilerError):
            builder._compile(unimported_source)
    finally:
        INITIAL_SCOPE.pop(alias, None)


def test_import_resolution_does_not_execute_imported_module(tmp_path):
    marker = tmp_path / "import-executed"
    imported_module = tmp_path / "contract_support.py"
    imported_module.write_text(f"""\
open({str(marker)!r}, "w").write("executed")
VALUE = 1
""")
    contract = tmp_path / "contract.py"
    source = """\
from contract_support import *

def validator(_: None) -> int:
    return VALUE
"""
    contract.write_text(source)

    RewriteImport(filename=str(contract)).visit(ast.parse(source))

    assert not marker.exists()


def test_binary_size_check_does_not_interpolate_baseline_path_into_shell(
    tmp_path, monkeypatch
):
    baseline = tmp_path / "baseline; touch shell-executed"
    baseline.write_text("{}")
    spec = importlib.util.spec_from_file_location(
        "check_binary_sizes",
        REPOSITORY_ROOT / "scripts/check_binary_sizes.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    commands = []
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda command, **kwargs: commands.append((command, kwargs)),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_binary_sizes.py", "--baseline-file", str(baseline)],
    )

    module.main()

    assert commands == [
        (
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/binary_size_tracker.py"),
                "compare",
                "--baseline-file",
                str(baseline),
            ],
            {"check": False},
        )
    ]


def test_compiler_fails_closed_when_python_disables_assertions(tmp_path):
    contract = tmp_path / "contract.py"
    contract.write_text("""\
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    pass
""")

    result = subprocess.run(
        [sys.executable, "-O", "-m", "opshin", "compile", str(contract)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode != 0
    assert "requires Python assertions" in result.stderr
