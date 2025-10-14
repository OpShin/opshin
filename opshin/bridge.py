"""Bridging tools between uplc and opshin"""

from functools import wraps

import re

import uplc.ast
from pycardano import PlutusData, RawCBOR

from opshin.std.bls12_381 import (
    BLS12381G1Element,
    BLS12381G2Element,
    BLS12381MillerLoopResult,
)


def to_uplc_builtin(a):
    if isinstance(a, bool):
        return uplc.ast.BuiltinBool(a)
    if isinstance(a, int):
        return uplc.ast.BuiltinInteger(a)
    if isinstance(a, str):
        return uplc.ast.BuiltinString(a)
    if isinstance(a, bytes):
        return uplc.ast.BuiltinByteString(a)
    if isinstance(a, list):
        return uplc.ast.BuiltinList(list(map(to_uplc_builtin, a)))
    if isinstance(a, PlutusData):
        return uplc.ast.data_from_cbor(a.to_cbor())
    if isinstance(a, BLS12381G1Element):
        return uplc.ast.BuiltinBLS12381G1Element(a._value)
    if isinstance(a, BLS12381G2Element):
        return uplc.ast.BuiltinBLS12381G2Element(a._value)
    if isinstance(a, BLS12381MillerLoopResult):
        return uplc.ast.BuiltinBLS12381Mlresult(a._value)
    raise NotImplementedError(f"Cannot convert {a} to uplc builtin")


def to_python(a):
    if (
        isinstance(a, uplc.ast.BuiltinInteger)
        or isinstance(a, uplc.ast.BuiltinString)
        or isinstance(a, uplc.ast.BuiltinByteString)
        or isinstance(a, uplc.ast.BuiltinBool)
    ):
        return a.value
    if isinstance(a, uplc.ast.BuiltinUnit):
        return None
    # TODO how to remap dict? use type annotations?
    if isinstance(a, uplc.ast.BuiltinList):
        return list(map(to_python, a.values))
    # TODO how to remap data? use type annotations?
    if isinstance(a, uplc.ast.PlutusData):
        return RawCBOR(uplc.ast.plutus_cbor_dumps(a))
    if isinstance(a, uplc.ast.BuiltinBLS12381G1Element):
        return BLS12381G1Element(a.value)
    if isinstance(a, uplc.ast.BuiltinBLS12381G2Element):
        return BLS12381G2Element(a.value)
    if isinstance(a, uplc.ast.BuiltinBLS12381Mlresult):
        return BLS12381MillerLoopResult(a.value)
    raise NotImplementedError(f"Cannot convert {a} to python")


def to_uplc_fun_name(snake_case_fun_name: str) -> str:
    fun_parts = []
    orig_name = snake_case_fun_name
    for match in re.finditer("[^_]+", orig_name):
        # keep underscore if starts/ends with decimal
        sub_part = match.group(0)
        if re.match(r"\d", sub_part[0]) and fun_parts and fun_parts[-1] != "_":
            fun_parts.append("_")
        fun_parts.append(sub_part.capitalize())
        if re.match(r"\d", sub_part[-1]):
            fun_parts.append("_")
    if fun_parts and fun_parts[-1] == "_":
        fun_parts.pop(-1)

    CamelCaseFunName = "".join(fun_parts)
    if CamelCaseFunName.startswith("Verify") and CamelCaseFunName.endswith(
        "_Signature"
    ):
        CamelCaseFunName = CamelCaseFunName.removesuffix("_Signature") + "Signature"
    return CamelCaseFunName


def wraps_builtin(func):
    snake_case_fun_name = func.__name__
    CamelCaseFunName = to_uplc_fun_name(snake_case_fun_name)

    @wraps(func)
    def wrapped(*args):
        """
        A UPLC builtin that was wrapped to be available in OpShin/Python.
        The type annotation of the original function is preserved.
        """
        uplc_fun = uplc.ast.BuiltInFun.__dict__[CamelCaseFunName]
        return to_python(
            uplc.ast.BuiltInFunEvalMap[uplc_fun](*(map(to_uplc_builtin, args)))
        )

    return wrapped
