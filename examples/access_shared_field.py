from eopsin.prelude import *


@dataclass()
class A(PlutusData):
    CONSTR_ID = 0
    fee: int


@dataclass()
class B(PlutusData):
    CONSTR_ID = 1
    fee: int


def validator(x: Union[A, B]) -> None:
    assert x.fee >= 1000000
