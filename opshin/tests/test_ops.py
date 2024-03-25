import unittest

import cbor2
import hypothesis
import pycardano
from frozendict import frozendict
import frozenlist as fl
from hypothesis import example, given
from hypothesis import strategies as st

from uplc import ast as uplc, eval as uplc_eval
from uplc.ast import (
    PlutusMap,
    PlutusConstr,
    PlutusList,
    PlutusInteger,
    PlutusByteString,
)

from . import PLUTUS_VM_PROFILE
from .utils import eval_uplc, eval_uplc_value, Unit
from .. import compiler

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)

from opshin.ledger.api_v2 import (
    FinitePOSIXTime,
    PosInfPOSIXTime,
    UpperBoundPOSIXTime,
    FalseData,
    TrueData,
)


def frozenlist(l):
    l = fl.FrozenList(l)
    l.freeze()
    return l


pos_int = st.integers(min_value=0, max_value=2**64 - 1)


uplc_data_integer = st.builds(PlutusInteger, st.integers())
uplc_data_bytestring = st.builds(PlutusByteString, st.binary())


def rec_data_strategies(uplc_data):
    uplc_data_list = st.builds(lambda x: PlutusList(frozenlist(x)), st.lists(uplc_data))
    uplc_data_constr = st.builds(
        lambda x, y: PlutusConstr(x, frozenlist(y)),
        pos_int,
        st.lists(uplc_data),
    )
    uplc_data_map = st.builds(
        PlutusMap,
        st.dictionaries(
            st.one_of(
                uplc_data_integer, uplc_data_bytestring
            ),  # TODO technically constr is legal too, but causes hashing error
            uplc_data,
            dict_class=frozendict,
        ),
    )
    return st.one_of(uplc_data_map, uplc_data_list, uplc_data_constr)


uplc_data = st.recursive(
    st.one_of(uplc_data_bytestring, uplc_data_integer),
    rec_data_strategies,
    max_leaves=4,
)
uplc_data_list = st.builds(lambda x: PlutusList(frozenlist(x)), st.lists(uplc_data))

# TODO fix handling of these strings
formattable_text = st.from_regex(r"\A((?!['\\])[ -~])*\Z")


class OpTest(unittest.TestCase):
    @given(x=st.booleans(), y=st.booleans())
    def test_and_bool(self, x, y):
        source_code = """
def validator(x: bool, y: bool) -> bool:
    return x and y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(bool(ret), x and y, "and returned wrong value")

    @given(x=st.booleans(), y=st.booleans())
    def test_or_bool(self, x, y):
        source_code = """
def validator(x: bool, y: bool) -> bool:
    return x or y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(bool(ret), x or y, "or returned wrong value")

    @given(x=st.booleans())
    def test_not_bool(self, x):
        source_code = """
def validator(x: bool) -> bool:
    return not x
            """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(bool(ret), not x, "not returned wrong value")

    @given(x=st.integers())
    def test_usub_int(self, x):
        source_code = """
def validator(x: int) -> int:
    return -x
            """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(ret, -x, "not returned wrong value")

    @given(x=st.integers())
    def test_uadd_int(self, x):
        source_code = """
def validator(x: int) -> int:
    return +x
            """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(ret, +x, "not returned wrong value")

    @given(x=st.integers())
    def test_not_int(self, x):
        source_code = """
def validator(x: int) -> bool:
    return not x
            """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(bool(ret), not x, "not returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_add_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> int:
    return x + y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x + y, "+ returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_sub_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> int:
    return x - y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x - y, "- returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_mul_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> int:
    return x * y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x * y, "* returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_div_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> int:
    return x // y
            """
        try:
            exp = x // y
        except ZeroDivisionError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y)
        except Exception:
            ret = None
        self.assertEqual(ret, exp, "// returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_mod_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> int:
    return x % y
            """
        try:
            exp = x % y
        except ZeroDivisionError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y)
        except Exception:
            ret = None
        self.assertEqual(ret, exp, "% returned wrong value")

    @given(x=st.integers(), y=st.integers(min_value=0, max_value=20))
    def test_pow_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> int:
    return x ** y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x**y, "** returned wrong value")

    @given(x=st.integers(), y=st.integers(min_value=-20, max_value=-1))
    def test_neg_pow_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> int:
    return x ** y
            """
        try:
            eval_uplc_value(source_code, x, y)
            fail = True
        except Exception:
            fail = False
        self.assertFalse(fail, "** worked with negative exponent")

    @given(x=st.binary(), y=st.binary())
    def test_add_bytes(self, x, y):
        source_code = """
def validator(x: bytes, y: bytes) -> bytes:
    return x + y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x + y, "+ returned wrong value")

    @given(x=st.text(), y=st.text())
    def test_add_str(self, x, y):
        source_code = """
def validator(x: str, y: str) -> str:
    return x + y
            """
        ret = eval_uplc_value(source_code, x.encode("utf8"), y.encode("utf8")).decode(
            "utf8"
        )
        self.assertEqual(ret, x + y, "+ returned wrong value")

    @given(x=st.binary(), y=st.integers(), z=st.integers())
    @example(b"\x00", -2, 0)
    @example(b"1234", 1, 2)
    @example(b"1234", 2, 4)
    @example(b"1234", 2, 2)
    @example(b"1234", 3, 3)
    @example(b"1234", 3, 1)
    def test_slice_bytes(self, x, y, z):
        source_code = """
def validator(x: bytes, y: int, z: int) -> bytes:
    return x[y:z]
            """
        try:
            exp = x[y:z]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y, z)
        except:
            ret = None
        self.assertEqual(ret, exp, "byte slice returned wrong value")

    @given(x=st.binary(), y=st.integers())
    @example(b"\x00", -2)
    @example(b"1234", 1)
    @example(b"1234", 2)
    @example(b"1234", 2)
    @example(b"1234", 3)
    @example(b"1234", 3)
    def test_slice_bytes_lower(self, x, y):
        source_code = """
def validator(x: bytes, y: int) -> bytes:
    return x[y:]
            """
        try:
            exp = x[y:]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y)
        except:
            ret = None
        self.assertEqual(ret, exp, "byte slice returned wrong value")

    @given(x=st.binary(), y=st.integers())
    @example(b"\x00", 0)
    @example(b"1234", 2)
    @example(b"1234", 4)
    @example(b"1234", 2)
    @example(b"1234", 3)
    @example(b"1234", 1)
    def test_slice_bytes_upper(self, x, y):
        source_code = """
def validator(x: bytes, y: int) -> bytes:
    return x[:y]
            """
        try:
            exp = x[:y]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y)
        except:
            ret = None
        self.assertEqual(ret, exp, "byte slice returned wrong value")

    @given(x=st.binary())
    @example(b"\x00")
    @example(b"1234")
    @example(b"1234")
    @example(b"1234")
    @example(b"1234")
    @example(b"1234")
    def test_slice_bytes_full(self, x):
        source_code = """
def validator(x: bytes) -> bytes:
    return x[:]
            """
        try:
            exp = x[:]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x)
        except:
            ret = None
        self.assertEqual(ret, exp, "byte slice returned wrong value")

    @given(x=st.binary(), y=st.integers())
    @example(b"1234", 0)
    @example(b"1234", 1)
    @example(b"1234", -1)
    def test_index_bytes(self, x, y):
        source_code = """
def validator(x: bytes, y: int) -> int:
    return x[y]
            """
        try:
            exp = x[y]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y)
        except:
            ret = None
        self.assertEqual(ret, exp, "byte index returned wrong value")

    @given(xs=st.lists(st.integers()), y=st.integers())
    @example(xs=[0], y=-1)
    @example(xs=[0], y=0)
    def test_index_list(self, xs, y):
        source_code = """
from typing import Dict, List, Union
def validator(x: List[int], y: int) -> int:
    return x[y]
            """
        try:
            exp = xs[y]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs, y)
        except Exception as e:
            ret = None
        self.assertEqual(ret, exp, "list index returned wrong value")

    @given(x=st.lists(st.integers(), max_size=20), y=st.integers(), z=st.integers())
    @example([0], -2, 0)
    @example([1, 2, 3, 4], 1, 2)
    @example([1, 2, 3, 4], 2, 4)
    @example([1, 2, 3, 4], 2, 2)
    @example([1, 2, 3, 4], 3, 3)
    @example([1, 2, 3, 4], 3, 1)
    def test_slice_list(self, x, y, z):
        source_code = """
def validator(x: List[int], y: int, z: int) -> List[int]:
    return x[y:z]
            """
        try:
            exp = x[y:z]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y, z)
        except:
            ret = None
        self.assertEqual(
            ret,
            [PlutusInteger(x) for x in exp] if exp is not None else exp,
            "list slice returned wrong value",
        )

    @given(x=st.lists(st.integers(), max_size=20), y=st.integers())
    @example([0], -2)
    @example([1, 2, 3, 4], 1)
    @example([1, 2, 3, 4], 2)
    @example([1, 2, 3, 4], 2)
    @example([1, 2, 3, 4], 3)
    @example([1, 2, 3, 4], 3)
    def test_slice_list_lower(self, x, y):
        source_code = """
def validator(x: List[int], y: int) -> List[int]:
    return x[y:]
            """
        try:
            exp = x[y:]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y)
        except:
            ret = None
        self.assertEqual(
            ret,
            [PlutusInteger(x) for x in exp] if exp is not None else exp,
            "list slice returned wrong value",
        )

    @given(x=st.lists(st.integers(), max_size=20), y=st.integers())
    @example([0], 0)
    @example([1, 2, 3, 4], 2)
    @example([1, 2, 3, 4], 4)
    @example([1, 2, 3, 4], 2)
    @example([1, 2, 3, 4], 3)
    @example([1, 2, 3, 4], 1)
    def test_slice_list_upper(self, x, y):
        source_code = """
def validator(x: List[int], y: int) -> List[int]:
    return x[:y]
            """
        try:
            exp = x[:y]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y)
        except:
            ret = None
        self.assertEqual(
            ret,
            [PlutusInteger(x) for x in exp] if exp is not None else exp,
            "list slice returned wrong value",
        )

    @given(x=st.lists(st.integers(), max_size=20))
    @example([0])
    @example([1, 2, 3, 4])
    @example([1, 2, 3, 4])
    @example([1, 2, 3, 4])
    @example([1, 2, 3, 4])
    @example([1, 2, 3, 4])
    def test_slice_list_full(self, x):
        source_code = """
def validator(x: List[int]) -> List[int]:
    return x[:]
            """
        try:
            exp = x[:]
        except IndexError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x)
        except:
            ret = None
        self.assertEqual(
            ret,
            [PlutusInteger(x) for x in exp] if exp is not None else exp,
            "list slice returned wrong value",
        )

    @given(xs=st.lists(st.integers()), y=st.integers())
    @example(xs=[0, 1], y=-1)
    @example(xs=[0, 1], y=0)
    def test_in_list_int(self, xs, y):
        source_code = """
from typing import Dict, List, Union
def validator(x: List[int], y: int) -> bool:
    return y in x
            """
        ret = eval_uplc_value(source_code, xs, y)
        self.assertEqual(ret, y in xs, "list in returned wrong value")

    @given(xs=st.lists(st.binary()), y=st.binary())
    def test_in_list_bytes(self, xs, y):
        source_code = """
from typing import Dict, List, Union
def validator(x: List[bytes], y: bytes) -> bool:
    return y in x
            """
        ret = eval_uplc_value(source_code, xs, y)
        self.assertEqual(ret, y in xs, "list in returned wrong value")

    @given(xs=uplc_data_list, y=uplc_data)
    def test_in_list_data(self, xs, y):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
def validator(x: List[Anything], y: Anything) -> bool:
    return y in x
            """
        ret = eval_uplc_value(source_code, xs, y)
        self.assertEqual(ret, y in xs.value, "list in returned wrong value")

    @given(xs=uplc_data_list, y=uplc_data)
    def test_not_in_list_data(self, xs, y):
        source_code = """
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData
def validator(x: List[Anything], y: Anything) -> bool:
    return y not in x
            """
        ret = eval_uplc_value(source_code, xs, y)
        self.assertEqual(ret, y not in xs.value, "list not in returned wrong value")

    @given(xs=st.lists(st.integers()), y=st.integers())
    @example(xs=[0, 1], y=-1)
    @example(xs=[0, 1], y=0)
    def test_not_in_list_int(self, xs, y):
        source_code = """
from typing import Dict, List, Union
def validator(x: List[int], y: int) -> bool:
    return y not in x
            """
        ret = eval_uplc_value(source_code, xs, y)
        self.assertEqual(ret, y not in xs, "list not in returned wrong value")

    @given(xs=st.lists(st.binary()), y=st.binary())
    def test_not_in_list_bytes(self, xs, y):
        source_code = """
from typing import Dict, List, Union
def validator(x: List[bytes], y: bytes) -> bool:
    return y not in x
            """
        ret = eval_uplc_value(source_code, xs, y)
        self.assertEqual(ret, y not in xs, "list not in returned wrong value")

    @given(x=st.lists(st.integers()))
    def test_not_list(self, x):
        source_code = """
def validator(x: List[int]) -> bool:
    return not x
            """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(bool(ret), not x, "not returned wrong value")

    @given(x=st.binary(), y=st.binary())
    def test_eq_bytes(self, x, y):
        source_code = """
def validator(x: bytes, y: bytes) -> bool:
    return x == y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x == y, "bytes eq returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_eq_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> bool:
    return x == y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x == y, "int eq returned wrong value")

    @given(x=st.text(), y=st.text())
    def test_eq_str(self, x, y):
        source_code = """
def validator(x: str, y: str) -> bool:
    return x == y
            """
        ret = eval_uplc_value(source_code, x.encode("utf8"), y.encode("utf8"))
        self.assertEqual(ret, x == y, "str eq returned wrong value")

    @given(x=st.booleans(), y=st.booleans())
    def test_eq_bool(self, x, y):
        source_code = """
def validator(x: bool, y: bool) -> bool:
    return x == y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x == y, "bool eq returned wrong value")

    @given(x=uplc_data, y=uplc_data)
    def test_eq_data(self, x, y):
        source_code = """
from opshin.prelude import *

def validator(x: Anything, y: Anything) -> bool:
    return x == y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x == y, "any eq returned wrong value")

    @given(x=st.booleans(), y=st.integers())
    def test_eq_bool_int(self, x, y):
        source_code = """
def validator(x: bool, y: int) -> bool:
    return x == y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x == y, "bool eq int returned wrong value")

    @given(x=st.text(), y=st.text())
    def test_neq_str(self, x, y):
        source_code = """
def validator(x: str, y: str) -> bool:
    return x != y
            """
        ret = eval_uplc_value(source_code, x.encode("utf8"), y.encode("utf8"))
        self.assertEqual(ret, x != y, "str neq returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_neq_int(self, x, y):
        source_code = """
def validator(x: int, y: int) -> bool:
    return x != y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x != y, "int neq returned wrong value")

    @given(x=st.binary(), y=st.binary())
    def test_neq_bytes(self, x, y):
        source_code = """
def validator(x: bytes, y: bytes) -> bool:
    return x != y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x != y, "bytes neq returned wrong value")

    @given(x=st.booleans(), y=st.booleans())
    def test_neq_bool(self, x, y):
        source_code = """
def validator(x: bool, y: bool) -> bool:
    return x != y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x != y, "bool neq returned wrong value")

    @given(x=st.booleans(), y=st.integers())
    def test_neq_bool_int(self, x, y):
        source_code = """
def validator(x: bool, y: int) -> bool:
    return x != y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x != y, "bool neq int returned wrong value")

    @given(x=uplc_data, y=uplc_data)
    def test_neq_data(self, x, y):
        source_code = """
from opshin.prelude import *

def validator(x: Anything, y: Anything) -> bool:
    return x != y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x != y, "any neq returned wrong value")

    @given(x=st.integers(min_value=0, max_value=150), y=st.text())
    def test_mul_int_str(self, x, y):
        source_code = """
def validator(x: int, y: str) -> str:
    return x * y
            """
        ret = eval_uplc_value(source_code, x, y.encode("utf8"))
        self.assertEqual(ret.decode("utf8"), x * y, "* returned wrong value")

    @given(x=st.text(), y=st.integers(min_value=0, max_value=150))
    def test_mul_str_int(self, x, y):
        source_code = """
def validator(x: str, y: int) -> str:
    return x * y
            """
        ret = eval_uplc_value(source_code, x.encode("utf8"), y)
        self.assertEqual(ret.decode("utf8"), x * y, "* returned wrong value")

    @given(x=st.integers(min_value=0, max_value=150), y=st.binary())
    def test_mul_int_bytes(self, x, y):
        source_code = """
def validator(x: int, y: bytes) -> bytes:
    return x * y
        """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x * y, "bytes int multiplication returned wrong value")

    @given(x=st.binary(), y=st.integers(min_value=0, max_value=150))
    def test_mul_bytes_int(self, x, y):
        source_code = """
def validator(x: bytes, y: int) -> bytes:
    return x * y
            """
        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, x * y, "* returned wrong value")

    @given(
        xs=st.lists(st.integers(), max_size=20), ys=st.lists(st.integers(), max_size=20)
    )
    def test_add_list(self, xs, ys):
        source_code = """
def validator(x: List[int], y: List[int]) -> List[int]:
    return x + y
            """
        ret = eval_uplc_value(source_code, xs, ys)
        self.assertEqual(
            ret,
            [PlutusInteger(x) for x in xs] + [PlutusInteger(y) for y in ys],
            "+ returned wrong value",
        )

    @given(x=st.integers())
    def test_fmt_int(self, x):
        source_code = """
def validator(x: int) -> str:
    return f"{x}"
    """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(
            ret.decode("utf8"), f"{x}", "int string formatting returned wrong value"
        )

    @given(x=st.booleans())
    def test_fmt_bool(self, x):
        source_code = """
def validator(x: bool) -> str:
    return f"{x}"
    """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(
            ret.decode("utf8"), f"{x}", "bool string formatting returned wrong value"
        )

    @given(x=st.text())
    def test_fmt_str(self, x):
        source_code = """
def validator(x: str) -> str:
    return f"{x}"
            """
        ret = eval_uplc_value(source_code, x.encode("utf8"))
        self.assertEqual(
            ret.decode("utf8"), f"{x}", "string string formatting returned wrong value"
        )

    @given(x=st.binary())
    @example(b"'")
    @example(b'"')
    @example(b"\\")
    @example(b"\r")
    @example(b"\n")
    @example(b"\t")
    @example(b"\x7f")
    def test_fmt_bytes(self, x):
        source_code = """
def validator(x: bytes) -> str:
    return f"{x}"
        """
        ret = eval_uplc_value(source_code, x).decode("utf8")
        if b"'" not in x:
            self.assertEqual(
                ret, f"{x}", "bytes string formatting returned wrong value"
            )
        else:
            # NOTE: formally this is a bug where we do not have the same semantics as python
            # specifically when ' is contained in the string we do not change the quotation marks
            self.assertEqual(
                eval(ret), x, "bytes string formatting returned wrong value"
            )

    @given(x=st.none())
    def test_fmt_none(self, x):
        source_code = """
def validator(x: None) -> str:
    return f"{x}"
            """
        ret = eval_uplc_value(source_code, Unit()).decode("utf8")
        self.assertEqual(ret, f"{x}", "none string formatting returned wrong value")

    @given(
        x=st.builds(
            UpperBoundPOSIXTime,
            st.one_of(
                st.builds(FinitePOSIXTime, st.integers()), st.builds(PosInfPOSIXTime)
            ),
            st.one_of(st.builds(TrueData), st.builds(FalseData)),
        )
    )
    @example(UpperBoundPOSIXTime(PosInfPOSIXTime(), TrueData()))
    def test_fmt_dataclass(self, x: UpperBoundPOSIXTime):
        source_code = """
from opshin.prelude import *

def validator(x: UpperBoundPOSIXTime) -> str:
    return f"{x}"
            """

        ret = eval_uplc_value(source_code, x).decode("utf8")
        self.assertEqual(
            ret, f"{x}", "several element string formatting returned wrong value"
        )

    @given(x=st.integers(), y=st.integers())
    def test_fmt_multiple(self, x, y):
        source_code = """
def validator(x: int, y: int) -> str:
    return f"a{x}b{y}c"
            """
        ret = eval_uplc_value(source_code, x, y).decode("utf8")
        self.assertEqual(
            ret, f"a{x}b{y}c", "several element string formatting returned wrong value"
        )

    @given(x=st.lists(st.integers()))
    @example([])
    @example([0])
    def test_fmt_tuple_int(self, x):
        params = [f"a{i}" for i in range(len(x))]
        source_code = f"""
def validator({",".join(p + ": int" for p in params)}) -> str:
    return f"{{({"".join(p + "," for p in params)})}}"
            """
        ret = eval_uplc_value(source_code, *x if x else [0]).decode("utf8")
        exp = f"{tuple(x)}"
        self.assertEqual(
            ret, exp, "integer tuple string formatting returned wrong value"
        )

    @given(xs=st.lists(formattable_text))
    def test_fmt_tuple_str(self, xs):
        # TODO strings are not properly escaped here
        params = [f"a{i}" for i in range(len(xs))]
        source_code = f"""
def validator({",".join(p + ": str" for p in params)}) -> str:
    return f"{{({"".join(p + "," for p in params)})}}"
            """
        ret = eval_uplc_value(
            source_code, *(x.encode("utf8") for x in xs) if xs else [0]
        ).decode("utf8")
        exp = f"{tuple(xs)}"
        self.assertEqual(ret, exp, "tuple string formatting returned wrong value")

    @given(x=st.integers(), y=st.integers())
    def test_fmt_pair_int(self, x, y):
        source_code = f"""
def validator(x: int, y: int) -> str:
    a = ""
    for p in {{x:y}}.items():
        a = f"{{p}}"
    return a
            """
        exp = f"{(x, y)}"
        ret = eval_uplc_value(source_code, x, y).decode("utf8")
        self.assertEqual(
            ret, exp, "integer tuple string formatting returned wrong value"
        )

    @given(x=formattable_text, y=formattable_text)
    def test_fmt_pair_str(self, x, y):
        # TODO strings are not properly escaped here
        source_code = f"""
def validator(x: str, y: str) -> str:
    a = ""
    for p in {{x:y}}.items():
        a = f"{{p}}"
    return a
            """
        exp = f"{(x, y)}"
        ret = eval_uplc_value(source_code, x.encode("utf8"), y.encode("utf8")).decode(
            "utf8"
        )
        self.assertEqual(
            ret, exp, "string tuple string formatting returned wrong value"
        )

    @given(xs=st.lists(formattable_text))
    @example([])
    @example(["x"])
    def test_fmt_list_str(self, xs):
        # TODO strings are not properly escaped here
        source_code = """
from opshin.prelude import *

def validator(x: List[str]) -> str:
    return f"{x}"
            """
        exp = f"{list(xs)}"
        ret = eval_uplc_value(source_code, [x.encode("utf8") for x in xs]).decode(
            "utf8"
        )
        self.assertEqual(ret, exp, "string list string formatting returned wrong value")

    @given(xs=st.lists(st.integers()))
    @example([])
    @example([0])
    def test_fmt_list_int(self, xs):
        source_code = """
from opshin.prelude import *

def validator(x: List[int]) -> str:
    return f"{x}"
            """
        exp = f"{list(xs)}"
        ret = eval_uplc_value(source_code, xs).decode("utf8")
        self.assertEqual(
            ret, exp, "integer list string formatting returned wrong value"
        )

    @given(x=st.dictionaries(st.integers(), st.integers()))
    def test_not_dict(self, x):
        source_code = """
def validator(x: Dict[int, int]) -> bool:
    return not x
            """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(bool(ret), not x, "not returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.integers()), y=st.integers())
    def test_index_dict(self, xs, y):
        source_code = """
from typing import Dict, List, Union
def validator(x: Dict[int, int], y: int) -> int:
    return x[y]
            """
        try:
            exp = xs[y]
        except KeyError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs, y)
        except Exception as e:
            ret = None
        self.assertEqual(ret, exp, "list index returned wrong value")

    @given(xs=st.dictionaries(formattable_text, st.integers()))
    @example(dict())
    @example({"": 0})
    def test_fmt_dict_int(self, xs):
        # TODO strings are not properly escaped here
        source_code = """
from opshin.prelude import *

def validator(x: Dict[str, int]) -> str:
    return f"{x}"
            """
        exp = f"{dict(xs)}"
        ret = eval_uplc_value(
            source_code, {k.encode("utf8"): v for k, v in xs.items()}
        ).decode("utf8")
        self.assertEqual(ret, exp, "dict string formatting returned wrong value")

    @given(x=uplc_data)
    @example(PlutusByteString(b""))
    @example(PlutusConstr(0, [PlutusByteString(b"'")]))
    @example(
        PlutusMap({PlutusInteger(1): PlutusMap({}), PlutusInteger(0): PlutusMap({})})
    )
    def test_fmt_any(self, x):
        x_cbor = uplc.plutus_cbor_dumps(x)
        x_data = pycardano.RawPlutusData(cbor2.loads(x_cbor))
        source_code = """
def validator(x: Anything) -> str:
    return f"{x}"
            """
        # NOTE: this is technically a deviation from the semantics of pycardano but I expect the pycardano semantics to change soon
        exp = f"RawPlutusData(data={repr(x_data.data)})"
        ret = eval_uplc_value(source_code, pycardano.RawCBOR(x_cbor)).decode("utf8")
        if "\\'" in ret:
            RawPlutusData = pycardano.RawPlutusData
            CBORTag = cbor2.CBORTag
            self.assertEqual(
                eval(ret), x_data, "raw cbor string formatting returned wrong value"
            )
        else:
            self.assertEqual(
                ret, exp, "raw cbor string formatting returned wrong value"
            )

    @given(x=st.text())
    def test_not_string(self, x):
        source_code = """
def validator(x: str) -> bool:
    return not x
            """
        ret = eval_uplc_value(source_code, x.encode("utf8"))
        self.assertEqual(bool(ret), not x, "not returned wrong value")

    @given(x=st.binary())
    def test_not_bytes(self, x):
        source_code = """
def validator(x: bytes) -> bool:
    return not x
            """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(bool(ret), not x, "not returned wrong value")

    def test_not_unit(self):
        source_code = """
def validator(x: None) -> bool:
    return not x
            """
        ret = eval_uplc_value(source_code, uplc.BuiltinUnit())
        self.assertEqual(bool(ret), not None, "not returned wrong value")
