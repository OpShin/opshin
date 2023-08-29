from parameterized import parameterized

from uplc import ast as uplc, eval as uplc_eval
from ... import compiler


@parameterized.expand(
    [
        [[0, 1]],
        [[0]],
        [[0, 1, 2]],
    ]
)
def test_integrity_check(xs):
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int
    bar: int

def validator(x: B) -> None:
    check_integrity(x)
"""
    ast = compiler.parse(source_code)
    code = compiler.compile(ast).compile()
    code = uplc.Apply(code, uplc.PlutusConstr(1, [uplc.PlutusInteger(x) for x in xs]))
    try:
        uplc_eval(code)
    except:
        res = False
    else:
        res = True
    assert res == (len(xs) == 2)
