import unittest
import ast
from typing import Dict, List

import hypothesis
import pytest
from hypothesis import given
from hypothesis import strategies as st

from opshin import DEFAULT_CONFIG
from opshin.ledger.api_v3 import *

from .. import PLUTUS_VM_PROFILE
from ..test_misc import A
from ..utils import DEFAULT_TEST_CONFIG, eval_uplc_raw

hypothesis.settings.load_profile(PLUTUS_VM_PROFILE)


def to_int(x):
    if isinstance(x, A):
        return 5
    elif isinstance(x, int):
        return 6
    elif isinstance(x, bytes):
        return 7
    elif isinstance(x, List):
        return 8
    elif isinstance(x, Dict):
        return 9
    return False


union_types = st.sampled_from([A(0), 10, b"foo", [1, 2, 3, 4, 5], {1: 2, 2: 3}])


class Union_tests(unittest.TestCase):
    def test_Union_expansion(
        self,
    ):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if isinstance(x, int):
        k = x + 1
    else:
        k = len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    k = x + 1
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, 4, config=euo_config)
        target = eval_uplc_raw(target_code, 4, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    @hypothesis.given(st.sampled_from(range(4, 7)))
    def test_Union_expansion_BoolOp_and(self, x):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if isinstance(x, int) and x > 5:
        k = x + 1
    elif isinstance(x, int):
        k = x - 1
    else:
        k = len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    if x > 5:
        k = x +1
    else:
        k = x - 1
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, x, config=euo_config)
        target = eval_uplc_raw(target_code, x, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    @hypothesis.given(st.sampled_from(range(4, 7)))
    def test_Union_expansion_BoolOp_or(self, x):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if isinstance(x, bytes) or x == 2:
        k = 2
    elif isinstance(x, int):
        k = x - 1
    else:
        k = len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    if x == 2:
        k = x +1
    else:
        k = x - 1
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, x, config=euo_config)
        target = eval_uplc_raw(target_code, x, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    @hypothesis.given(st.sampled_from([b"123", b"1"]), st.sampled_from([b"123", b"1"]))
    def test_Union_expansion_BoolOp_and_all(self, x, y):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes], y: Union[int, bytes]) -> int:
    if isinstance(x, bytes) and isinstance(y, bytes):
        k = len(x) + len(y)
    else:
        k = 2
    return k

def validator(x: bytes, y: bytes) -> int:
    return foo(x, y)
    """
        target_code = """
from typing import Dict, List, Union

def foo(x: bytes, y: bytes) -> int:
    k = len(x) + len(y)
    return k

def validator(x: bytes, y: bytes) -> int:
    return foo(x, y)
    """
        config = DEFAULT_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, x, y, config=euo_config)
        target = eval_uplc_raw(target_code, x, y, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    @hypothesis.given(st.sampled_from(range(4, 7)))
    @hypothesis.example(4)
    @hypothesis.example(5)
    @hypothesis.example(6)
    @pytest.mark.skip(
        """
        This fails because union expansion is broken. produces this code:

    from typing import Dict, List, Union

    def foo(x: Union[int, bytes]) -> int:
        if isinstance(x, bytes) or isinstance(x, int):
            k = 2
        else:
            k = len(x)
        return k

    def foo+_int(x: int) -> int:
        k = 2
        return k

    def foo+_bytes(x: bytes) -> int:
        k = 2
        return k

    def validator(x: int) -> int:
        return foo(x)
        """
    )
    def test_Union_expansion_BoolOp_or_all(self, x):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if isinstance(x, bytes) or isinstance(x, int):
        k = 2
    else:
        k = len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    k = 2
    return k

def validator(x: int) -> int:
    return foo(x)
    """
        config = DEFAULT_CONFIG.update(constant_folding=True)
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, x, config=euo_config)
        target = eval_uplc_raw(target_code, x, config=config)

        self.assertEqual(source.result, target.result)
        self.assertLessEqual(source.cost.cpu, target.cost.cpu)
        self.assertLessEqual(source.cost.memory, target.cost.memory)

    def test_Union_expansion_UnaryOp(
        self,
    ):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    if not isinstance(x, int):
        k = len(x)
    else:
        k = x + 1
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    k = x + 1
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        config = DEFAULT_TEST_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, 4, config=euo_config)
        target = eval_uplc_raw(target_code, 4, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    def test_Union_expansion_IfExp(
        self,
    ):
        source_code = """
from typing import Dict, List, Union

def foo(x: Union[int, bytes]) -> int:
    k = x + 1 if isinstance(x, int) else len(x)
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        target_code = """
from typing import Dict, List, Union

def foo(x: int) -> int:
    k = x + 1
    return k

def validator(x: int) -> int:
    return foo(x)
"""
        config = DEFAULT_TEST_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, 4, config=euo_config)
        target = eval_uplc_raw(target_code, 4, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    @given(x_in=st.sampled_from([4, b"123"]), y_in=st.sampled_from([4, b"123"]))
    def test_Union_expansion_multiple(self, x_in, y_in):
        x = type(x_in).__name__
        y = type(y_in).__name__
        source_code = f"""
from typing import Dict, List, Union

def foo(x: Union[int, bytes], y: Union[int, bytes]) -> int:
    if isinstance(x, int):
        if isinstance(y, int):
            k = x + y
        else:
            k = x + len(y)
    else:
        if isinstance(y, int):
            k = len(x) + y
        else:
            k = len(x) + len(y)
    return k

def validator(x: {x}, y: {y} ) -> int:
    return foo(x, y)
"""
        target_code = f"""
from typing import Dict, List, Union

def foo(x: {x}, y: {y} ) -> int:
    k = {'len(x)' if x=='bytes' else 'x'} + {'len(y)' if y == 'bytes' else 'y'}
    return k

def validator(x: {x},  y: {y}) -> int:
    return foo(x, y)
"""
        config = DEFAULT_TEST_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, x_in, y_in, config=euo_config)
        target = eval_uplc_raw(target_code, x_in, y_in, config=config)

        self.assertEqual(source.result, target.result)
        self.assertEqual(source.cost.cpu, target.cost.cpu)
        self.assertEqual(source.cost.memory, target.cost.memory)

    @given(st.sampled_from([0, 1, 2, 3]), st.sampled_from([b"", b"ab", b"abcd"]))
    def test_Union_expansion_mutual_recursion(self, n, b):
        source_code = """
from typing import Union

def even_i(x: Union[int, bytes], n: int) -> int:
    if n == 0:
        if isinstance(x, int):
            return x
        if isinstance(x, bytes):
            return len(x)
    if isinstance(x, bytes):
        return odd_i(x[2:], n - 1)
    else:
        return odd_i(x + 1, n - 1)

def odd_i(x: Union[int, bytes], n: int) -> int:
    if n == 0:
        if isinstance(x, int):
            return x + 100
        if isinstance(x, bytes):
            return len(x) + 100
    if isinstance(x, bytes):
        return even_i(len(x[2:]), n - 1)
    else:
        return even_i(bytes([x + 1]), n - 1)

def validator(x: bytes, n: int) -> int:
    return even_i(x, n)
"""
        target_code = """
def even_i_int(x: int, n: int) -> int:
    if n == 0:
        return x
    return odd_i_int(x + 1, n - 1)

def odd_i_int(x: int, n: int) -> int:
    if n == 0:
        return x + 100
    return even_i_bytes(bytes([x + 1]), n - 1)

def even_i_bytes(x: bytes, n: int) -> int:
    if n == 0:
        return len(x)
    return odd_i_bytes(x[2:], n - 1)

def odd_i_bytes(x: bytes, n: int) -> int:
    if n == 0:
        return len(x) + 100
    return even_i_int(len(x[2:]), n - 1)

def validator(x: bytes, n: int) -> int:
    return even_i_bytes(x, n)
"""
        config = DEFAULT_TEST_CONFIG
        euo_config = config.update(expand_union_types=True)
        source = eval_uplc_raw(source_code, b, n, config=euo_config)
        target = eval_uplc_raw(target_code, b, n, config=config)

        self.assertEqual(source.result, target.result)
        self.assertLessEqual(source.cost.cpu, target.cost.cpu)
        self.assertLessEqual(source.cost.memory, target.cost.memory)
