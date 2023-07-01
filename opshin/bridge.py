""" Bridging tools between uplc and opshin """
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
    if isinstance(a, dict):
        return uplc.ast.BuiltinList(
            list([(to_uplc_builtin(k), to_uplc_builtin(v)) for k, v in a])
        )
    if isinstance(a, PlutusData):
        return uplc.ast.data_from_cbor(a.to_cbor())


def to_python(a):
    if (
        isinstance(a, uplc.ast.BuiltinInteger)
        or isinstance(a, uplc.ast.BuiltinString)
        or isinstance(a, uplc.ast.BuiltinByteString)
    ):
        return a.value
    # TODO how to remap dict? use type annotations?
    if isinstance(a, uplc.ast.BuiltinList):
        return list(map(to_python, a.values))
    # TODO how to remap data? use type annotations?
    if isinstance(a, uplc.ast.PlutusData):
        return RawCBOR(uplc.ast.plutus_cbor_dumps(a))


def wraps_builtin(func):
    snake_case_fun_name = func.__name__
    CamelCaseFunName = "".join(
        p.capitalize() for p in re.split(r"_(?!\d)", snake_case_fun_name)
    )

    def wrapped(*args):
        uplc_fun = uplc.ast.BuiltInFun.__dict__[CamelCaseFunName]
        return to_python(
            uplc.ast.BuiltInFunEvalMap[uplc_fun](*(map(to_uplc_builtin, args)))
        )

    return wrapped
