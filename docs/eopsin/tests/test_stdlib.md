# Test Stdlib

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Tests](./index.md#tests) /
Test Stdlib

> Auto-generated documentation for [eopsin.tests.test_stdlib](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py) module.

- [Test Stdlib](#test-stdlib)
  - [StdlibTest](#stdlibtest)
    - [StdlibTest().test_constant_bool](#stdlibtest()test_constant_bool)
    - [StdlibTest().test_constant_bytestring](#stdlibtest()test_constant_bytestring)
    - [StdlibTest().test_constant_integer](#stdlibtest()test_constant_integer)
    - [StdlibTest().test_constant_string](#stdlibtest()test_constant_string)
    - [StdlibTest().test_constant_unit](#stdlibtest()test_constant_unit)
    - [StdlibTest().test_dict_keys](#stdlibtest()test_dict_keys)
    - [StdlibTest().test_dict_values](#stdlibtest()test_dict_values)
    - [StdlibTest().test_str_decode](#stdlibtest()test_str_decode)
    - [StdlibTest().test_str_encode](#stdlibtest()test_str_encode)

## StdlibTest

[Show source in test_stdlib.py:12](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L12)

#### Signature

```python
class StdlibTest(unittest.TestCase):
    ...
```

### StdlibTest().test_constant_bool

[Show source in test_stdlib.py:160](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L160)

#### Signature

```python
@given(st.booleans())
def test_constant_bool(self, x: bool):
    ...
```

### StdlibTest().test_constant_bytestring

[Show source in test_stdlib.py:96](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L96)

#### Signature

```python
@given(xs=st.binary())
@example(b"dc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2")
def test_constant_bytestring(self, xs):
    ...
```

### StdlibTest().test_constant_integer

[Show source in test_stdlib.py:113](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L113)

#### Signature

```python
@given(xs=st.integers())
def test_constant_integer(self, xs):
    ...
```

### StdlibTest().test_constant_string

[Show source in test_stdlib.py:129](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L129)

#### Signature

```python
@given(xs=st.text())
def test_constant_string(self, xs):
    ...
```

### StdlibTest().test_constant_unit

[Show source in test_stdlib.py:145](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L145)

#### Signature

```python
def test_constant_unit(self):
    ...
```

### StdlibTest().test_dict_keys

[Show source in test_stdlib.py:13](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L13)

#### Signature

```python
@given(xs=st.dictionaries(st.integers(), st.binary()))
def test_dict_keys(self, xs):
    ...
```

### StdlibTest().test_dict_values

[Show source in test_stdlib.py:34](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L34)

#### Signature

```python
@given(xs=st.dictionaries(st.integers(), st.binary()))
def test_dict_values(self, xs):
    ...
```

### StdlibTest().test_str_decode

[Show source in test_stdlib.py:72](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L72)

#### Signature

```python
@given(xs=st.binary())
def test_str_decode(self, xs):
    ...
```

### StdlibTest().test_str_encode

[Show source in test_stdlib.py:55](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/tests/test_stdlib.py#L55)

#### Signature

```python
@given(xs=st.text())
def test_str_encode(self, xs):
    ...
```