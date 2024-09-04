from parameterized import parameterized

from uplc import ast as uplc, eval as uplc_eval
from ..utils import eval_uplc


@parameterized.expand(
    [
        [[0, 1]],
        [[0]],
        [[0, 1, 2]],
        [[b"hello", 0]],
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
    obj = uplc.PlutusConstr(
        1,
        [
            uplc.PlutusInteger(x) if isinstance(x, int) else uplc.PlutusByteString(x)
            for x in xs
        ],
    )
    try:
        eval_uplc(source_code, obj)
    except Exception as e:
        print(e)
        res = False
    else:
        res = True
    assert res == (len(xs) == 2 and all(isinstance(x, int) for x in xs))


@parameterized.expand(
    [
        [0],
        [1],
        [2],
    ]
)
def test_integrity_check_list(bar_constr):
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass()
class A(PlutusData):
    CONSTR_ID = 1
    
@dataclass()
class C(PlutusData):
    CONSTR_ID = 0

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    bar: Union[A, C]

def validator(x: B) -> None:
    check_integrity(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [uplc.PlutusConstr(bar_constr, [])],
    )
    try:
        eval_uplc(source_code, obj)
    except:
        res = False
    else:
        res = True
    assert res == (bar_constr in (0, 1))


@parameterized.expand(
    [
        [[0, 1], [1, 1, 1]],
        [[b"hello"], [1, 1]],
        [[0, 1, 2], [1, 0]],
    ]
)
def test_integrity_check_list(foobar, bar_constrs):
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass()
class A(PlutusData):
    CONSTR_ID = 1

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: List[int]
    bar: List[A]

def validator(x: B) -> None:
    check_integrity(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [
            uplc.PlutusList(
                [
                    (
                        uplc.PlutusInteger(x)
                        if isinstance(x, int)
                        else uplc.PlutusByteString(x)
                    )
                    for x in foobar
                ]
            ),
            uplc.PlutusList([uplc.PlutusConstr(c, []) for c in bar_constrs]),
        ],
    )
    try:
        eval_uplc(source_code, obj)
    except:
        res = False
    else:
        res = True
    assert res == (
        all(isinstance(x, int) for x in foobar) and all(c == 1 for c in bar_constrs)
    )


@parameterized.expand(
    [
        [[0, 1, 2], [1, 1, 1]],
        # check for incorrect type in keys
        [[b"hello", 1], [1, 1]],
        # check for incorrect type in values
        [[1, 2], [1, b"hello"]],
    ]
)
def test_integrity_check_dict(keys, values):
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: Dict[int, int]

def validator(x: B) -> None:
    check_integrity(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [
            uplc.PlutusMap(
                {
                    (
                        uplc.PlutusInteger(x)
                        if isinstance(x, int)
                        else uplc.PlutusByteString(x)
                    ): (
                        uplc.PlutusInteger(y)
                        if isinstance(y, int)
                        else uplc.PlutusByteString(y)
                    )
                    for x, y in zip(keys, values)
                },
            ),
        ],
    )
    try:
        eval_uplc(source_code, obj)
    except:
        res = False
    else:
        res = True
    assert res == (
        all(isinstance(x, int) for x in keys + values) and len(set(keys)) == len(keys)
    )


def test_integrity_check_rename():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
from opshin.std.integrity import check_integrity as integ

@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    foobar: int

def validator(x: B) -> None:
    integ(x)
"""
    obj = uplc.PlutusConstr(
        1,
        [uplc.PlutusInteger(1)],
    )
    eval_uplc(source_code, obj)


# TODO implement better way to check for uniqueness test in dict keys
