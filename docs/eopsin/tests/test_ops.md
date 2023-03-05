# Test Ops

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Tests](./index.md#tests) /
Test Ops

> Auto-generated documentation for [eopsin.tests.test_ops](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py) module.

- [Test Ops](#test-ops)
  - [OpTest](#optest)
    - [OpTest().test_add_bytes](#optest()test_add_bytes)
    - [OpTest().test_add_int](#optest()test_add_int)
    - [OpTest().test_add_str](#optest()test_add_str)
    - [OpTest().test_and_bool](#optest()test_and_bool)
    - [OpTest().test_div_int](#optest()test_div_int)
    - [OpTest().test_eq_bool](#optest()test_eq_bool)
    - [OpTest().test_eq_bytes](#optest()test_eq_bytes)
    - [OpTest().test_eq_bytes](#optest()test_eq_bytes-1)
    - [OpTest().test_eq_str](#optest()test_eq_str)
    - [OpTest().test_in_list_bytes](#optest()test_in_list_bytes)
    - [OpTest().test_in_list_int](#optest()test_in_list_int)
    - [OpTest().test_index_bytes](#optest()test_index_bytes)
    - [OpTest().test_index_list](#optest()test_index_list)
    - [OpTest().test_mod_int](#optest()test_mod_int)
    - [OpTest().test_mul_int](#optest()test_mul_int)
    - [OpTest().test_not_bool](#optest()test_not_bool)
    - [OpTest().test_or_bool](#optest()test_or_bool)
    - [OpTest().test_pow_int](#optest()test_pow_int)
    - [OpTest().test_slice_bytes](#optest()test_slice_bytes)
    - [OpTest().test_sub_int](#optest()test_sub_int)
    - [OpTest().test_usub_int](#optest()test_usub_int)

## OpTest

[Show source in test_ops.py:13](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L13)

#### Signature

```python
class OpTest(unittest.TestCase):
    ...
```

### OpTest().test_add_bytes

[Show source in test_ops.py:198](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L198)

#### Signature

```python
@given(x=st.binary(), y=st.binary())
def test_add_bytes(self, x, y):
    ...
```

### OpTest().test_add_int

[Show source in test_ops.py:82](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L82)

#### Signature

```python
@given(x=st.integers(), y=st.integers())
def test_add_int(self, x, y):
    ...
```

### OpTest().test_add_str

[Show source in test_ops.py:215](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L215)

#### Signature

```python
@given(x=st.text(), y=st.text())
def test_add_str(self, x, y):
    ...
```

### OpTest().test_and_bool

[Show source in test_ops.py:14](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L14)

#### Signature

```python
@given(x=st.booleans(), y=st.booleans())
def test_and_bool(self, x, y):
    ...
```

### OpTest().test_div_int

[Show source in test_ops.py:133](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L133)

#### Signature

```python
@given(x=st.integers(), y=st.integers())
def test_div_int(self, x, y):
    ...
```

### OpTest().test_eq_bool

[Show source in test_ops.py:435](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L435)

#### Signature

```python
@given(x=st.booleans(), y=st.booleans())
def test_eq_bool(self, x, y):
    ...
```

### OpTest().test_eq_bytes

[Show source in test_ops.py:372](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L372)

#### Signature

```python
@given(x=st.binary(), y=st.binary())
def test_eq_bytes(self, x, y):
    ...
```

### OpTest().test_eq_bytes

[Show source in test_ops.py:393](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L393)

#### Signature

```python
@given(x=st.integers(), y=st.integers())
def test_eq_bytes(self, x, y):
    ...
```

### OpTest().test_eq_str

[Show source in test_ops.py:414](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L414)

#### Signature

```python
@given(x=st.text(), y=st.text())
def test_eq_str(self, x, y):
    ...
```

### OpTest().test_in_list_bytes

[Show source in test_ops.py:350](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L350)

#### Signature

```python
@given(xs=st.lists(st.binary()), y=st.binary())
def test_in_list_bytes(self, xs, y):
    ...
```

### OpTest().test_in_list_int

[Show source in test_ops.py:326](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L326)

#### Signature

```python
@given(xs=st.lists(st.integers()), y=st.integers())
@example(xs=[0, 1], y=-1)
@example(xs=[0, 1], y=0)
def test_in_list_int(self, xs, y):
    ...
```

### OpTest().test_index_bytes

[Show source in test_ops.py:269](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L269)

#### Signature

```python
@given(x=st.binary(), y=st.integers())
@example(b"1234", 0)
@example(b"1234", 1)
@example(b"1234", -1)
def test_index_bytes(self, x, y):
    ...
```

### OpTest().test_index_list

[Show source in test_ops.py:296](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L296)

#### Signature

```python
@given(xs=st.lists(st.integers()), y=st.integers())
@example(xs=[0], y=-1)
@example(xs=[0], y=0)
def test_index_list(self, xs, y):
    ...
```

### OpTest().test_mod_int

[Show source in test_ops.py:157](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L157)

#### Signature

```python
@given(x=st.integers(), y=st.integers())
def test_mod_int(self, x, y):
    ...
```

### OpTest().test_mul_int

[Show source in test_ops.py:116](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L116)

#### Signature

```python
@given(x=st.integers(), y=st.integers())
def test_mul_int(self, x, y):
    ...
```

### OpTest().test_not_bool

[Show source in test_ops.py:48](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L48)

#### Signature

```python
@given(x=st.booleans())
def test_not_bool(self, x):
    ...
```

### OpTest().test_or_bool

[Show source in test_ops.py:31](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L31)

#### Signature

```python
@given(x=st.booleans(), y=st.booleans())
def test_or_bool(self, x, y):
    ...
```

### OpTest().test_pow_int

[Show source in test_ops.py:181](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L181)

#### Signature

```python
@given(x=st.integers(), y=st.integers(min_value=0, max_value=20))
def test_pow_int(self, x, y):
    ...
```

### OpTest().test_slice_bytes

[Show source in test_ops.py:235](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L235)

#### Signature

```python
@given(x=st.binary(), y=st.integers(), z=st.integers())
@example(b"\x00", -2, 0)
@example(b"1234", 1, 2)
@example(b"1234", 2, 4)
@example(b"1234", 2, 2)
@example(b"1234", 3, 3)
@example(b"1234", 3, 1)
def test_slice_bytes(self, x, y, z):
    ...
```

### OpTest().test_sub_int

[Show source in test_ops.py:99](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L99)

#### Signature

```python
@given(x=st.integers(), y=st.integers())
def test_sub_int(self, x, y):
    ...
```

### OpTest().test_usub_int

[Show source in test_ops.py:65](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_ops.py#L65)

#### Signature

```python
@given(x=st.integers())
def test_usub_int(self, x):
    ...
```