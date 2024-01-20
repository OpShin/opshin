import hypothesis
import unittest

from hypothesis import example, given
from hypothesis import strategies as st

from . import PLUTUS_VM_PROFILE
from .utils import eval_uplc, eval_uplc_value, Unit

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)


class BuiltinTest(unittest.TestCase):
    @given(xs=st.lists(st.booleans()))
    def test_all(self, xs):
        source_code = """
def validator(x: List[bool]) -> bool:
    return all(x)
            """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(bool(ret), all(xs), "all returned wrong value")

    @given(xs=st.lists(st.booleans()))
    def test_any(self, xs):
        source_code = """
def validator(x: List[bool]) -> bool:
    return any(x)
        """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(bool(ret), any(xs), "any returned wrong value")

    @given(i=st.integers())
    def test_abs(self, i):
        source_code = """
def validator(x: int) -> int:
    return abs(x)
        """
        ret = eval_uplc_value(source_code, i)
        self.assertEqual(ret, abs(i), "abs returned wrong value")

    @given(
        xs=st.one_of(
            st.lists(st.integers()), st.lists(st.integers(min_value=0, max_value=255))
        )
    )
    def test_bytes_int_list(self, xs):
        source_code = """
def validator(x: List[int]) -> bytes:
    return bytes(x)
        """
        try:
            exp = bytes(xs)
        except ValueError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs)
        except:
            ret = None
        self.assertEqual(ret, exp, "bytes (integer list) returned wrong value")

    @given(x=st.integers(min_value=-1000, max_value=1000))
    def test_bytes_int(self, x):
        source_code = """
def validator(x: int) -> bytes:
    return bytes(x)
        """
        try:
            exp = bytes(x)
        except ValueError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x)
        except:
            ret = None
        self.assertEqual(ret, exp, "bytes (integer) returned wrong value")

    @given(x=st.binary())
    def test_bytes_bytes(self, x):
        source_code = """
def validator(x: bytes) -> bytes:
    return bytes(x)
        """
        try:
            exp = bytes(x)
        except ValueError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x)
        except:
            ret = None
        self.assertEqual(ret, exp, "bytes (bytes) returned wrong value")

    @given(i=st.integers())
    @example(256)
    @example(0)
    def test_chr(self, i):
        source_code = """
def validator(x: int) -> str:
    return chr(x)
        """
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        try:
            i_unicode = chr(i).encode("utf8")
        except (ValueError, OverflowError):
            i_unicode = None
        try:
            ret = eval_uplc_value(source_code, i)
        except:
            ret = None
        self.assertEqual(ret, i_unicode, "chr returned wrong value")

    @given(x=st.integers())
    @example(0)
    @example(-1)
    @example(100)
    def test_hex(self, x):
        source_code = """
def validator(x: int) -> str:
    return hex(x)
        """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(ret.decode("utf8"), hex(x), "hex returned wrong value")

    @given(
        xs=st.one_of(
            st.builds(lambda x: str(x), st.integers()),
            st.from_regex(r"\A(?!\s).*(?<!\s)\Z", fullmatch=True),
        )
    )
    @example("")
    @example("10_00")
    @example("_")
    @example("_1")
    @example("-")
    @example("+123")
    @example("-_")
    @example("0_")
    # @example("0\n")  # stripping is broken
    def test_int_string(self, xs: str):
        source_code = """
def validator(x: str) -> int:
    return int(x)
        """
        try:
            exp = int(xs)
        except ValueError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs.encode("utf8"))
        except Exception as e:
            ret = None
        self.assertEqual(ret, exp, "int (str) returned wrong value")

    @given(xs=st.booleans())
    def test_int_bool(self, xs: bool):
        source_code = """
def validator(x: bool) -> int:
    return int(x)
        """
        try:
            exp = int(xs)
        except ValueError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs)
        except:
            ret = None
        self.assertEqual(ret, exp, "int (bool) returned wrong value")

    @given(xs=st.integers())
    def test_int_int(self, xs: int):
        source_code = """
def validator(x: int) -> int:
    return int(x)
        """
        try:
            exp = int(xs)
        except ValueError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs)
        except:
            ret = None
        self.assertEqual(ret, exp, "int (int) returned wrong value")

    @given(i=st.binary())
    def test_len_bytestring(self, i):
        source_code = """
def validator(x: bytes) -> int:
    return len(x)
        """
        # UPLC lambdas may only take one argument at a time, so we evaluate by repeatedly applying
        ret = eval_uplc_value(source_code, i)
        self.assertEqual(ret, len(i), "len (bytestring) returned wrong value")

    @given(xs=st.lists(st.integers()))
    def test_len_lists(self, xs):
        source_code = """
def validator(x: List[int]) -> int:
    return len(x)
        """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(ret, len(xs), "len returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.integers()))
    def test_len_dicts(self, xs):
        source_code = """
def validator(x: Dict[int, int]) -> int:
    return len(x)
        """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(ret, len(xs), "len returned wrong value")

    @given(xs=st.lists(st.integers()))
    def test_len_tuples(self, xs):
        source_code = f"""
def validator(x: None) -> int:
    return len(({", ".join(map(str, xs))}{"," if len(xs) == 1 else ""}))
        """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(ret, len(xs), "len returned wrong value")

    @given(xs=st.lists(st.integers()))
    def test_max(self, xs):
        source_code = """
def validator(x: List[int]) -> int:
    return max(x)
        """
        try:
            exp = max(xs)
        except:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs)
        except:
            ret = None
        self.assertEqual(ret, exp, "max returned wrong value")

    @given(xs=st.lists(st.integers()))
    def test_min(self, xs):
        source_code = """
def validator(x: List[int]) -> int:
    return min(x)
        """
        try:
            exp = min(xs)
        except ValueError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, xs)
        except:
            ret = None
        self.assertEqual(ret, exp, "min returned wrong value")

    @given(x=st.integers(), y=st.integers(min_value=0, max_value=20))
    def test_pow(self, x: int, y: int):
        source_code = """
def validator(x: int, y: int) -> int:
    return pow(x, y) % 10000000000
        """
        try:
            exp = pow(x, y) % 10000000000
        except ValueError:
            exp = None
        try:
            ret = eval_uplc_value(source_code, x, y)
        except:
            ret = None
        self.assertEqual(ret, exp, "pow returned wrong value")

    @given(x=st.integers(), y=st.integers(min_value=-20, max_value=-1))
    def test_neg_pow(self, x: int, y: int):
        source_code = """
def validator(x: int, y: int) -> int:
    return pow(x, y) % 10000000000
        """
        try:
            eval_uplc_value(source_code, x, y)
            fail = True
        except Exception:
            fail = False
        self.assertFalse(fail, "pow worked on negative exponent")

    @given(x=st.integers())
    @example(0)
    @example(-1)
    @example(100)
    def test_oct(self, x):
        source_code = """
def validator(x: int) -> str:
    return oct(x)
        """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(ret.decode("utf8"), oct(x), "oct returned wrong value")

    @given(i=st.integers(max_value=100))
    def test_range(self, i):
        source_code = """
def validator(x: int) -> List[int]:
    return range(x)
        """
        ret = eval_uplc_value(source_code, i)
        self.assertEqual(
            [x.value for x in ret], list(range(i)), "sum returned wrong value"
        )

    @given(x=st.integers())
    @example(0)
    @example(-1)
    @example(100)
    def test_str_int(self, x):
        source_code = """
def validator(x: int) -> str:
    return str(x)
        """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(ret.decode("utf8"), str(x), "str returned wrong value")

    @given(x=st.booleans())
    def test_str_bool(self, x):
        source_code = """
def validator(x: bool) -> str:
    return str(x)
        """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(ret.decode("utf8"), str(x), "str returned wrong value")

    @given(xs=st.lists(st.integers()))
    def test_sum(self, xs):
        source_code = """
def validator(x: List[int]) -> int:
    return sum(x)
        """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(ret, sum(xs), "sum returned wrong value")

    @given(xs=st.lists(st.integers()))
    def test_reversed(self, xs):
        source_code = """
def validator(x: List[int]) -> List[int]:
    return reversed(x)
        """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(
            [r.value for r in ret], list(reversed(xs)), "reversed returned wrong value"
        )

    @given(x=st.integers())
    def test_bool_constr_int(self, x):
        source_code = """
def validator(x: int) -> bool:
    return bool(x)
        """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(bool(ret), bool(x), "bool (int) returned wrong value")

    @given(x=st.text())
    def test_bool_constr_str(self, x):
        source_code = """
def validator(x: str) -> bool:
    return bool(x)
        """
        ret = eval_uplc_value(source_code, x.encode("utf8"))
        self.assertEqual(bool(ret), bool(x), "bool (str) returned wrong value")

    @given(x=st.binary())
    def test_bool_constr_bytes(self, x):
        source_code = """
def validator(x: bytes) -> bool:
    return bool(x)
        """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(bool(ret), bool(x), "bool (bytes) returned wrong value")

    @given(x=st.none())
    def test_bool_constr_none(self, x):
        source_code = """
def validator(x: None) -> bool:
    return bool(x)
        """
        ret = eval_uplc_value(source_code, Unit())
        self.assertEqual(bool(ret), bool(x), "bool (none) returned wrong value")

    @given(x=st.booleans())
    def test_bool_constr_bool(self, x):
        source_code = """
def validator(x: bool) -> bool:
    return bool(x)
        """
        ret = eval_uplc_value(source_code, x)
        self.assertEqual(bool(ret), bool(x), "bool (bool) returned wrong value")

    @given(xs=st.lists(st.integers()))
    def test_bool_constr_list(self, xs):
        source_code = """
def validator(x: List[int]) -> bool:
    return bool(x)
        """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(bool(ret), bool(xs), "bool (list) returned wrong value")

    @given(xs=st.dictionaries(st.integers(), st.binary()))
    def test_bool_constr_dict(self, xs):
        source_code = """
def validator(x: Dict[int, str]) -> bool:
    return bool(x)
        """
        ret = eval_uplc_value(source_code, xs)
        self.assertEqual(bool(ret), bool(xs), "bool (list) returned wrong value")

    @given(x=st.integers(), y=st.booleans(), z=st.none())
    def test_print_compile(self, x, y, z):
        source_code = """
def validator(x: int, y: bool, z: None) -> None:
    print(x, y, z)
        """
        eval_uplc(source_code, x, y, Unit())
