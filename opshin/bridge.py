"""Bridging tools between uplc and opshin"""

from functools import wraps

import re

import uplc.ast
from pycardano import PlutusData, RawCBOR


def to_uplc_builtin(a):
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
    raise NotImplementedError(f"Cannot convert {a} to uplc builtin")


def to_python(a):
    if (
        isinstance(a, uplc.ast.BuiltinInteger)
        or isinstance(a, uplc.ast.BuiltinString)
        or isinstance(a, uplc.ast.BuiltinByteString)
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
    raise NotImplementedError(f"Cannot convert {a} to python")


def wraps_builtin(func):
    snake_case_fun_name = func.__name__
    CamelCaseFunName = "".join(
        p.capitalize() for p in re.split(r"_(?!\d)", snake_case_fun_name)
    )

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
