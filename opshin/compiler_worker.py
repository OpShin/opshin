import ast
import builtins
import subprocess
import sys
from dataclasses import dataclass

import cbor2
import uplc
from pluthon import compile as compile_pluthon

from . import compiler
from .compiler_config import CompilationConfig
from .util import CompilerError


@dataclass(frozen=True)
class CompilerWorker:
    source: str
    filename: str
    validator: str
    config: CompilationConfig

    ERROR_MARKER = b"OPSHIN_WORKER_ERROR:"

    def compile(self) -> uplc.ast.Program:
        timeout = self.config.constant_folding_timeout
        assert (
            timeout is not None and timeout > 0
        ), "constant_folding_timeout must be positive when constant folding is enabled"
        process = subprocess.Popen(
            [sys.executable, "-m", "opshin.compiler_worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            output, stderr = process.communicate(input=self._request(), timeout=timeout)
        except subprocess.TimeoutExpired as error:
            process.kill()
            process.communicate()
            raise CompilerError(
                TimeoutError(
                    "Compile-time constant evaluation exceeded its wall-clock "
                    f"budget of {timeout} seconds"
                ),
                ast.parse(self.source),
                "Constant folding",
            ) from error
        if process.returncode != 0:
            raise self._compiler_error(stderr)
        return uplc.unflatten(output)

    def _request(self) -> bytes:
        return cbor2.dumps(
            {
                "source": self.source,
                "filename": self.filename,
                "validator": self.validator,
                "config": self.config.__dict__,
            }
        )

    def _compiler_error(self, stderr: bytes) -> CompilerError:
        marker_offset = stderr.rfind(self.ERROR_MARKER)
        if marker_offset < 0:
            return CompilerError(
                RuntimeError(stderr.decode(errors="replace").strip()),
                ast.parse(self.source),
                "Constant folding",
            )
        payload = cbor2.loads(
            bytes.fromhex(
                stderr[marker_offset + len(self.ERROR_MARKER) :].strip().decode()
            )
        )
        error_type = getattr(builtins, payload["error_type"], RuntimeError)
        if not isinstance(error_type, type) or not issubclass(error_type, Exception):
            error_type = RuntimeError
        location = payload["location"]
        if location["kind"] == "Module":
            node = ast.parse(self.source)
        else:
            node = ast.Pass()
            for name in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
                setattr(node, name, location[name])
        return CompilerError(error_type(payload["message"]), node, payload["step"])

    @classmethod
    def run(cls) -> None:
        request = cbor2.loads(sys.stdin.buffer.read())
        config = CompilationConfig(**request["config"])
        try:
            source_ast = compiler.parse(request["source"], filename=request["filename"])
            program = compiler.compile(
                source_ast,
                filename=request["filename"],
                validator_function_name=request["validator"],
                config=config,
            )
            uplc_program = compile_pluthon(program, config)
        except CompilerError as error:
            cls._write_error(error)
            raise SystemExit(1)
        sys.stdout.buffer.write(uplc.flatten(uplc_program))

    @classmethod
    def _write_error(cls, error: CompilerError) -> None:
        node = error.node
        location = (
            {"kind": "Module"}
            if isinstance(node, ast.Module)
            else {
                "kind": type(node).__name__,
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "end_lineno": node.end_lineno,
                "end_col_offset": node.end_col_offset,
            }
        )
        payload = {
            "error_type": type(error.orig_err).__name__,
            "message": str(error.orig_err),
            "step": error.compilation_step,
            "location": location,
        }
        sys.stderr.buffer.write(cls.ERROR_MARKER + cbor2.dumps(payload).hex().encode())


if __name__ == "__main__":
    CompilerWorker.run()
