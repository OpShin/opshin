#!opshin
from opshin.prelude import *


@dataclass
class D2(PlutusData):
    CONSTR_ID = 0
    list_field: List[DatumHash]


def validator(d: D2) -> bool:
    return b"\x01" == d.list_field[0]
