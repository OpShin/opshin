# Test Builtins

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Tests](./index.md#tests) /
Test Builtins

> Auto-generated documentation for [eopsin.tests.test_builtins](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py) module.

- [Test Builtins](#test-builtins)
  - [BuiltinTest](#builtintest)
    - [BuiltinTest().test_abs](#builtintest()test_abs)
    - [BuiltinTest().test_all](#builtintest()test_all)
    - [BuiltinTest().test_any](#builtintest()test_any)
    - [BuiltinTest().test_bytes_int_list](#builtintest()test_bytes_int_list)
    - [BuiltinTest().test_chr](#builtintest()test_chr)
    - [BuiltinTest().test_hex](#builtintest()test_hex)
    - [BuiltinTest().test_int_string](#builtintest()test_int_string)
    - [BuiltinTest().test_int_string](#builtintest()test_int_string-1)
    - [BuiltinTest().test_len_bytestring](#builtintest()test_len_bytestring)
    - [BuiltinTest().test_len_lists](#builtintest()test_len_lists)
    - [BuiltinTest().test_max](#builtintest()test_max)
    - [BuiltinTest().test_min](#builtintest()test_min)
    - [BuiltinTest().test_oct](#builtintest()test_oct)
    - [BuiltinTest().test_pow](#builtintest()test_pow)
    - [BuiltinTest().test_range](#builtintest()test_range)
    - [BuiltinTest().test_reversed](#builtintest()test_reversed)
    - [BuiltinTest().test_str_int](#builtintest()test_str_int)
    - [BuiltinTest().test_sum](#builtintest()test_sum)

## BuiltinTest

[Show source in test_builtins.py:13](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L13)

#### Signature

```python
class BuiltinTest(unittest.TestCase):
    ...
```

### BuiltinTest().test_abs

[Show source in test_builtins.py:48](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L48)

#### Signature

```python
@given(i=st.integers())
def test_abs(self, i):
    ...
```

### BuiltinTest().test_all

[Show source in test_builtins.py:14](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L14)

#### Signature

```python
@given(xs=st.lists(st.booleans()))
def test_all(self, xs):
    ...
```

### BuiltinTest().test_any

[Show source in test_builtins.py:31](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L31)

#### Signature

```python
@given(xs=st.lists(st.booleans()))
def test_any(self, xs):
    ...
```

### BuiltinTest().test_bytes_int_list

[Show source in test_builtins.py:68](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L68)

#### Signature

```python
@given(
    xs=st.one_of(
        st.lists(st.integers()), st.lists(st.integers(min_value=0, max_value=255))
    )
)
def test_bytes_int_list(self, xs):
    ...
```

### BuiltinTest().test_chr

[Show source in test_builtins.py:95](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L95)

#### Signature

```python
@given(i=st.integers())
@example(256)
@example(0)
def test_chr(self, i):
    ...
```

### BuiltinTest().test_hex

[Show source in test_builtins.py:121](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L121)

#### Signature

```python
@given(x=st.integers())
@example(0)
@example(-1)
@example(100)
def test_hex(self, x):
    ...
```

### BuiltinTest().test_int_string

[Show source in test_builtins.py:141](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L141)

#### Signature

```python
@unittest.skip("Integer stripping is currently broken")
@given(xs=st.one_of(st.builds(lambda x,: str(x), st.integers()), st.text()))
@example("")
@example("10_00")
@example("_")
@example("_1")
@example("0\n")
def test_int_string(self, xs: str):
    ...
```

### BuiltinTest().test_int_string

[Show source in test_builtins.py:170](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L170)

#### Signature

```python
@parameterized.parameterized.expand(
    ["10_00", "00", "_", "_1", "-10238", "19293812983721837981", "jakjsdh"]
)
def test_int_string(self, xs: str):
    ...
```

### BuiltinTest().test_len_bytestring

[Show source in test_builtins.py:195](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L195)

#### Signature

```python
@given(i=st.binary())
def test_len_bytestring(self, i):
    ...
```

### BuiltinTest().test_len_lists

[Show source in test_builtins.py:212](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L212)

#### Signature

```python
@given(xs=st.lists(st.integers()))
def test_len_lists(self, xs):
    ...
```

### BuiltinTest().test_max

[Show source in test_builtins.py:229](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L229)

#### Signature

```python
@given(xs=st.lists(st.integers()))
def test_max(self, xs):
    ...
```

### BuiltinTest().test_min

[Show source in test_builtins.py:253](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L253)

#### Signature

```python
@given(xs=st.lists(st.integers()))
def test_min(self, xs):
    ...
```

### BuiltinTest().test_oct

[Show source in test_builtins.py:299](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L299)

#### Signature

```python
@given(x=st.integers())
@example(0)
@example(-1)
@example(100)
def test_oct(self, x):
    ...
```

### BuiltinTest().test_pow

[Show source in test_builtins.py:277](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L277)

#### Signature

```python
@given(x=st.integers(), y=st.integers(min_value=0, max_value=20))
def test_pow(self, x: int, y: int):
    ...
```

### BuiltinTest().test_range

[Show source in test_builtins.py:319](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L319)

#### Signature

```python
@given(i=st.integers(max_value=100))
def test_range(self, i):
    ...
```

### BuiltinTest().test_reversed

[Show source in test_builtins.py:373](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L373)

#### Signature

```python
@given(xs=st.lists(st.integers()))
def test_reversed(self, xs):
    ...
```

### BuiltinTest().test_str_int

[Show source in test_builtins.py:336](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L336)

#### Signature

```python
@given(x=st.integers())
@example(0)
@example(-1)
@example(100)
def test_str_int(self, x):
    ...
```

### BuiltinTest().test_sum

[Show source in test_builtins.py:356](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_builtins.py#L356)

#### Signature

```python
@given(xs=st.lists(st.integers()))
def test_sum(self, xs):
    ...
```