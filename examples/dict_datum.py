#!opshin
from opshin.prelude import *


# You need to enable hashing in order to allow the data to be the key of a dict
@dataclass(unsafe_hash=True)
class D(PlutusData):
    CONSTR_ID = 0
    p: bytes


@dataclass
class D2(PlutusData):
    CONSTR_ID = 0
    dict_field: Dict[D, int]


def validator(d: D2) -> bool:
    return (
        D(b"\x01") in d.dict_field.keys()
        and 2 in d.dict_field.values()
        and not D(b"") in d.dict_field.keys()
    )
