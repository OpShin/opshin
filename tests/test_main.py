import tempfile


def test_main_no_validator():
    source_code = """
from opshin.prelude import *

def val(context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "Contract has no function called 'validator'" in result.stderr


def test_main_wrong_syntax():
    source_code = """
from opshin.prelude import *

def val(context: ScriptContext -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "Could not import the input file" in result.stderr


def test_main_invalid_param():
    source_code = """
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py", "abbb"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "Could not parse parameter 0" in result.stderr


def test_main_invalid_param_type_cbor():
    source_code = """
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py", "00"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "Could not parse parameter 0" in result.stderr


def test_main_invalid_param_type_json():
    source_code = """
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py", '{"integer":0}'],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "Could not parse parameter 0" in result.stderr


def test_main_parse():
    source_code = """
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "parse", f"{tmpdir}/contract.py"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
        assert "successfully" in result.stdout


def test_main_type_error():
    source_code = """
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    return context.transaction
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "SyntaxError" in result.stderr
        assert (
            "Function annotated return type does not match actual return type"
            in result.stderr
        )


def test_main_build_lib():
    source_code = """
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "build", f"{tmpdir}/contract.py", "--lib"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "Cannot build a library" in result.stderr


def test_main_eval_logs_exception():
    source_code = """
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    print("Hello")
    assert False, "Failing on purpose"
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            [
                "opshin",
                "eval",
                f"{tmpdir}/contract.py",
                "d8799fd8799f9fd8799fd8799f582019895b96b5da29ecb09e6043b7fff42ef16406a3442848298cb1e900f54da37800ffd8799fd8799fd87a9f581ce876ac436a77d58ba0e3d3a318bf94526a607b4c64f140ed5db9b0f3ffd87a80ffa140a1401a002dc6c0d87b9fd8799f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffffd87a80ffffff809fd8799fd8799fd8799f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffd87a80ffa140a1401a0029ebc7d87980d87a80ffff1a0003daf9a080a0d8799fd8799fd87a9f1b00000199c3745c58ffd87a80ffd8799fd87a9f1b00000199c3839e98ffd87980ffff9f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffa1d87a9fd8799f582019895b96b5da29ecb09e6043b7fff42ef16406a3442848298cb1e900f54da37800ffff00a05820bf16a9ba49965f9eb23e13ff1af73df41d8cad82afabcd3dc59be9a40bd324f9a080d87a80d87a80ff00d87a9fd8799f582019895b96b5da29ecb09e6043b7fff42ef16406a3442848298cb1e900f54da37800ffd8799fd8799f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffffffff",
            ],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
        assert "EXCEPTION" in result.stdout
        assert "LOGS" in result.stdout
        assert "Hello" in result.stdout
        assert "Failing on purpose" in result.stdout
        assert "SUCCESS" not in result.stdout


def test_main_eval_logs_no_exception():
    source_code = """
from opshin.prelude import *

def validator(context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            [
                "opshin",
                "eval",
                f"{tmpdir}/contract.py",
                "d8799fd8799f9fd8799fd8799f582019895b96b5da29ecb09e6043b7fff42ef16406a3442848298cb1e900f54da37800ffd8799fd8799fd87a9f581ce876ac436a77d58ba0e3d3a318bf94526a607b4c64f140ed5db9b0f3ffd87a80ffa140a1401a002dc6c0d87b9fd8799f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffffd87a80ffffff809fd8799fd8799fd8799f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffd87a80ffa140a1401a0029ebc7d87980d87a80ffff1a0003daf9a080a0d8799fd8799fd87a9f1b00000199c3745c58ffd87a80ffd8799fd87a9f1b00000199c3839e98ffd87980ffff9f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffa1d87a9fd8799f582019895b96b5da29ecb09e6043b7fff42ef16406a3442848298cb1e900f54da37800ffff00a05820bf16a9ba49965f9eb23e13ff1af73df41d8cad82afabcd3dc59be9a40bd324f9a080d87a80d87a80ff00d87a9fd8799f582019895b96b5da29ecb09e6043b7fff42ef16406a3442848298cb1e900f54da37800ffd8799fd8799f581c25d14bb0185eedffcaa02cdd3bfa779bfc9df3555c64b0e91ed41273ffffffff",
            ],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
        assert "EXCEPTION" not in result.stdout
        assert "No logs" in result.stdout
        assert "SUCCESS" in result.stdout
        assert "con unit ()" in result.stdout
        assert "Python: None" in result.stdout


def test_error_for_params_without_explicit_specification():
    source_code = """
from opshin.prelude import *

def validator(datum: int, redeemer: int, context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert (
            "The validator is specified to expect 2 parameters for parameterization"
            in result.stderr
        )

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py", "--parameters", "2"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0


def test_error_for_params_bound_build():
    source_code = """
from opshin.prelude import *

def validator(owner: bytes, context: ScriptContext) -> None:
    pass
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/contract.py", "w") as f:
            f.write(source_code)
        import subprocess

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert (
            "The validator is specified to expect 1 parameters for parameterization"
            in result.stderr
        )

        result = subprocess.run(
            ["opshin", "compile", f"{tmpdir}/contract.py", "--parameters", "1"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
        result = subprocess.run(
            [
                "opshin",
                "compile",
                f"{tmpdir}/contract.py",
                '{"bytes":"abcd"}',
                "--parameters",
                "1",
            ],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0
        assert "The validator is specified to expect 0 parameters" in result.stderr

        result = subprocess.run(
            [
                "opshin",
                "compile",
                f"{tmpdir}/contract.py",
                '{"bytes":"abcd"}',
                "--parameters",
                "0",
            ],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode == 0
