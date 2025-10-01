from dataclasses import dataclass
import unittest

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from uplc import ast as uplc, eval as uplc_eval
from pycardano import PlutusData

from . import PLUTUS_VM_PROFILE
from .utils import eval_uplc, eval_uplc_value, Unit
from opshin import compiler, builder, CompilerError

settings.load_profile(PLUTUS_VM_PROFILE)


class StdlibTest(unittest.TestCase):
    @given(st.data())
    def test_dict_get(self, data):
        source_code = """
from typing import Dict, List, Union
def validator(x: Dict[int, bytes], y: int, z: bytes) -> bytes:
    return x.get(y, z)
            """
        x = data.draw(st.dictionaries(st.integers(), st.binary()))
        y = data.draw(st.one_of(st.sampled_from(sorted(x.keys()) + [0]), st.integers()))
        z = data.draw(st.binary())
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        ret = eval_uplc_value(source_code, x, y, z)
        self.assertEqual(ret, x.get(y, z), "dict.get returned wrong value")

    @given(st.data())
    def test_dict_subscript(self, data):
        source_code = """
from typing import Dict, List, Union
def validator(x: Dict[int, bytes], y: int) -> bytes:
    return x[y]
            """
        x = data.draw(st.dictionaries(st.integers(), st.binary()))
        y = data.draw(st.one_of(st.sampled_from(sorted(x.keys()) + [0]), st.integers()))
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            ret = eval_uplc_value(source_code, x, y)
        except RuntimeError:
            ret = None
        try:
            exp = x[y]
        except KeyError:
            exp = None
        self.assertEqual(ret, exp, "dict[] returned wrong value")

    @given(st.data())
    def test_list_index(self, data):
        source_code = """
from typing import Dict, List, Union
def validator(x: List[int], z: int) -> int:
    return x.index(z)
            """
        xs = data.draw(st.lists(st.integers()))
        z = data.draw(
            st.one_of(st.sampled_from(xs), st.integers())
            if len(xs) > 0
            else st.integers()
        )
        try:
            ret = eval_uplc_value(source_code, xs, z)
        except RuntimeError as e:
            ret = None
        try:
            exp = xs.index(z)
        except ValueError:
            exp = None
        self.assertEqual(ret, exp, "list.index returned wrong value")

    @given(st.integers(), st.binary(), st.integers(), st.binary())
    @example(1, b"abc", 2, b"def")
    def test_list_index(self, a_x, a_y, b_x, b_y):
        # ensure that (a_x, a_y) != (b_x, b_y)
        if a_x == b_x and a_y == b_y:
            b_x += 1
        source_code = """
from opshin.prelude import *

@dataclass
class Test(PlutusData):
    CONSTR_ID = 0
    x: int
    y: bytes

def validator(a_x: int, a_y: bytes, b_x: int, b_y: bytes) -> int:
    a: Test = Test(a_x, a_y)
    b: Test = Test(b_x, b_y)
    l: List[Test] = [a, b]

    return l.index(b)
            """

        try:
            ret = eval_uplc_value(source_code, a_x, a_y, b_x, b_y)
        except RuntimeError as e:
            ret = None
        exp = 1
        self.assertEqual(ret, exp, "list.index returned wrong value")

    def test_list_index_typemismatch(self):
        source_code = """
from opshin.prelude import *

@dataclass
class Test(PlutusData):
    CONSTR_ID = 0
    x: int
    y: bytes

def validator(b: int) -> int:
    a: Test = Test(b, b"hi")
    l: List[Test] = [a, a]

    return l.index(20)
                    """
        # should fail compilation
        with pytest.raises(CompilerError) as e:
            builder._compile(source_code)
        assert "signature" in str(e.value).lower()

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_keys(self, xs):
        source_code = """
from typing import Dict, List, Union
def validator(x: Dict[int, bytes]) -> List[int]:
    return x.keys()
            """
        ret = eval_uplc(source_code, xs)
        ret = [x.value for x in ret.value]
        self.assertEqual(ret, list(xs.keys()), "dict.keys returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_values(self, xs):
        source_code = """
from typing import Dict, List, Union
def validator(x: Dict[int, bytes]) -> List[bytes]:
    return x.values()
            """
        ret = eval_uplc(source_code, xs)
        ret = [x.value for x in ret.value]
        self.assertEqual(ret, list(xs.values()), "dict.keys returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_items_keys_sum(self, xs):
        source_code = """
from typing import Dict, List, Union
def validator(xs: Dict[int, bytes]) -> int:
    sum_keys = 0
    for x in xs.items():
        sum_keys += x[0]
    return sum_keys
"""
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(ret, sum(xs.keys()), "dict.items returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_dict_items_values_sum(self, xs):
        source_code = """
from typing import Dict, List, Union
def validator(xs: Dict[int, bytes]) -> bytes:
    sum_values = b""
    for x in xs.items():
        sum_values += x[1]
    return sum_values
"""
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(ret, b"".join(xs.values()), "dict.items returned wrong value")

    @given(xs=st.text())
    def test_str_encode(self, xs):
        source_code = """
def validator(x: str) -> bytes:
    return x.encode()
            """
        ret = eval_uplc_value(source_code, xs.encode("utf8"))
        self.assertEqual(ret, xs.encode(), "str.encode returned wrong value")

    @given(xs=st.binary())
    def test_bytes_decode(self, xs):
        source_code = """
def validator(x: bytes) -> str:
    return x.decode()
            """
        try:
            exp = xs.decode()
        except UnicodeDecodeError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs).decode()
        except UnicodeDecodeError:
            ret = None
        self.assertEqual(ret, exp, "bytes.decode returned wrong value")

    @given(xs=st.binary())
    def test_bytes_hex(self, xs):
        source_code = """
def validator(x: bytes) -> str:
    return x.hex()
            """
        ret = eval_uplc_value(source_code, xs).decode()
        self.assertEqual(ret, xs.hex(), "bytes.hex returned wrong value")

    @given(xs=st.binary())
    @example(b"dc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2")
    def test_constant_bytestring(self, xs):
        source_code = f"""
def validator(x: None) -> bytes:
    return {repr(xs)}
            """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(ret, xs, "literal bytes returned wrong value")

    @given(xs=st.integers())
    def test_constant_integer(self, xs):
        source_code = f"""
def validator(x: None) -> int:
    return {repr(xs)}
            """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(ret, xs, "literal integer returned wrong value")

    @given(xs=st.text())
    def test_constant_string(self, xs):
        source_code = f"""
def validator(x: None) -> str:
    return {repr(xs)}
            """
        ret = eval_uplc_value(source_code, Unit()).decode()
        self.assertEqual(ret, xs, "literal string returned wrong value")

    def test_constant_unit(self):
        source_code = f"""
def validator(x: None) -> None:
    return None
            """
        ret = eval_uplc(source_code, Unit())
        self.assertEqual(
            ret,
            uplc.data_from_cbor(Unit().to_cbor()),
            "literal None returned wrong value",
        )

    @given(st.booleans())
    def test_constant_bool(self, x: bool):
        source_code = f"""
def validator(x: None) -> bool:
    return {repr(x)}
            """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(bool(ret), x, "literal bool returned wrong value")

    @given(st.integers(), st.binary())
    def test_plutusdata_to_cbor(self, x: int, y: bytes):
        source_code = f"""
from opshin.prelude import *

@dataclass
class Test(PlutusData):
    CONSTR_ID = 0
    x: int
    y: bytes

def validator(x: int, y: bytes) -> bytes:
    return Test(x, y).to_cbor()
            """

        @dataclass
        class Test(PlutusData):
            CONSTR_ID = 0
            x: int
            y: bytes

        ret = eval_uplc_value(source_code, x, y)
        self.assertEqual(ret, Test(x, y).to_cbor(), "to_cbor returned wrong value")

    @given(st.integers(), st.booleans())
    def test_union_to_cbor(self, x: int, z: bool):
        source_code = f"""
from opshin.prelude import *

@dataclass
class Test(PlutusData):
    CONSTR_ID = 1
    x: int
    y: bytes

@dataclass
class Test2(PlutusData):
    CONSTR_ID = 0
    x: int

def validator(x: int, z: bool) -> bytes:
    y: Union[Test, Test2] = Test2(x) if z else Test(x, b'')
    return y.to_cbor()
        """

        @dataclass
        class Test(PlutusData):
            CONSTR_ID = 1
            x: int
            y: bytes

        @dataclass
        class Test2(PlutusData):
            CONSTR_ID = 0
            x: int

        ret = eval_uplc_value(source_code, x, z)
        self.assertEqual(
            ret,
            Test2(x).to_cbor() if z else Test(x, b"").to_cbor(),
            "to_cbor returned wrong value",
        )


def test_tuple_invalid_slice_type():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def validator(x: int) -> int:
    l = (x, 1)
    return l[0:1][0]
"""
    with pytest.raises(CompilerError) as e:
        eval_uplc_value(source_code, 5)
    assert "subscript" in str(e.value)


def test_pair_invalid_slice_type():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def validator(x: int) -> int:
    l = {b"fst": x, b"snd": 1}.items()[0]
    return l[0:1][0]
"""
    with pytest.raises(CompilerError) as e:
        eval_uplc_value(source_code, 5)
    assert "subscript" in str(e.value)


def test_dict_invalid_slice_type():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def validator(x: int) -> int:
    l = {b"fst": x, b"snd": 1}
    x = l[0:1]
    return l["fst"]
"""
    with pytest.raises(CompilerError) as e:
        eval_uplc_value(source_code, 5)
    assert "subscript" in str(e.value)


def test_dict_invalid_subscript():
    source_code = """
from dataclasses import dataclass
from typing import Dict, List, Union
from pycardano import Datum as Anything, PlutusData

def validator(x: int) -> int:
    y = x[0]
    return x + 1
"""
    with pytest.raises(CompilerError) as e:
        eval_uplc_value(source_code, 5)
    assert "subscript" in str(e.value)


@given(st.data())
def test_tuple_subscript(data):
    x = data.draw(st.integers(min_value=1, max_value=10))
    y = data.draw(st.integers())
    i = data.draw(st.integers(min_value=-x * 2, max_value=(x - 1) * 2))
    # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
    source_code = f"""
def validator(y: int) -> int:
    x = ({','.join('y + ' + str(i) for i in range(x))},)
    return x[{i}]
            """
    try:
        ret = eval_uplc_value(source_code, y)
    except RuntimeError:
        ret = None
    try:
        exp = [y + j for j in range(x)][i]
    except KeyError:
        exp = None
    assert ret == exp, "tuple[] returned wrong value"


@given(
    x=st.dictionaries(st.binary(), st.integers(), max_size=5),
    i=st.sampled_from([-3, -2, -1, 0, 1, 2]),
    f=st.booleans(),
)
@example(
    x={b"first": 1, b"second": 2},
    i=1,
    f=False,
)
@example(
    x={},
    i=-2,
    f=False,
)
@example(
    x={},
    i=2,
    f=False,
)
def test_pair_subscript(x, i, f):
    # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
    source_code = f"""
from typing import Dict

def validator(x: Dict[bytes, int]) -> {"bytes" if i %2 == 0 else "int"}:
    y = {repr(b"") if i %2 == 0 else 0}
    for pair in x.items():
       y += pair[{i}]
    return y
"""
    try:
        ret = eval_uplc_value(
            source_code, x, config=compiler.DEFAULT_CONFIG.update(constant_folding=f)
        )
    except (RuntimeError, CompilerError) as e:
        ret = None
    try:
        if (i > 1 or i < -2) and not x:
            raise IndexError()
        exp = b"" if i % 2 == 0 else 0
        for pair in x.items():
            exp += pair[i]
    except (KeyError, IndexError) as e:
        exp = None
    assert ret == exp, f"pair[] returned wrong value for {x}, {i}"
