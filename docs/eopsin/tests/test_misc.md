# Test Misc

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Tests](./index.md#tests) /
Test Misc

> Auto-generated documentation for [eopsin.tests.test_misc](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py) module.

- [Test Misc](#test-misc)
  - [MiscTest](#misctest)
    - [MiscTest().test_assert_sum_contract_fail](#misctest()test_assert_sum_contract_fail)
    - [MiscTest().test_assert_sum_contract_succeed](#misctest()test_assert_sum_contract_succeed)
    - [MiscTest().test_complex_datum_correct_vals](#misctest()test_complex_datum_correct_vals)
    - [MiscTest().test_datum_cast](#misctest()test_datum_cast)
    - [MiscTest().test_dict_datum](#misctest()test_dict_datum)
    - [MiscTest().test_dual_use_compile](#misctest()test_dual_use_compile)
    - [MiscTest().test_fib_iter](#misctest()test_fib_iter)
    - [MiscTest().test_fib_rec](#misctest()test_fib_rec)
    - [MiscTest().test_gift_contract_fail](#misctest()test_gift_contract_fail)
    - [MiscTest().test_gift_contract_succeed](#misctest()test_gift_contract_succeed)
    - [MiscTest().test_hello_world](#misctest()test_hello_world)
    - [MiscTest().test_list_comprehension_all](#misctest()test_list_comprehension_all)
    - [MiscTest().test_list_comprehension_even](#misctest()test_list_comprehension_even)
    - [MiscTest().test_list_datum_correct_vals](#misctest()test_list_datum_correct_vals)
    - [MiscTest().test_list_expr](#misctest()test_list_expr)
    - [MiscTest().test_marketplace_compile](#misctest()test_marketplace_compile)
    - [MiscTest().test_marketplace_compile_fail](#misctest()test_marketplace_compile_fail)
    - [MiscTest().test_mult_for](#misctest()test_mult_for)
    - [MiscTest().test_mult_while](#misctest()test_mult_while)
    - [MiscTest().test_overopt_removedeadvar](#misctest()test_overopt_removedeadvar)
    - [MiscTest().test_parameterized_compile](#misctest()test_parameterized_compile)
    - [MiscTest().test_recursion](#misctest()test_recursion)
    - [MiscTest().test_redefine_constr](#misctest()test_redefine_constr)
    - [MiscTest().test_script_context_repr_correct](#misctest()test_script_context_repr_correct)
    - [MiscTest().test_showcase](#misctest()test_showcase)
    - [MiscTest().test_sum](#misctest()test_sum)
    - [MiscTest().test_union_type_all_records_same_constr](#misctest()test_union_type_all_records_same_constr)
    - [MiscTest().test_union_type_attr_access_all_records](#misctest()test_union_type_attr_access_all_records)
    - [MiscTest().test_union_type_attr_access_all_records_same_constr](#misctest()test_union_type_attr_access_all_records_same_constr)
    - [MiscTest().test_union_type_attr_access_maximum_type](#misctest()test_union_type_attr_access_maximum_type)
    - [MiscTest().test_union_type_attr_anytype](#misctest()test_union_type_attr_anytype)
    - [MiscTest().test_wrap_into_generic_data](#misctest()test_wrap_into_generic_data)
    - [MiscTest().test_wrapping_contract_compile](#misctest()test_wrapping_contract_compile)
  - [fib](#fib)

## MiscTest

[Show source in test_misc.py:20](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L20)

#### Signature

```python
class MiscTest(unittest.TestCase):
    ...
```

### MiscTest().test_assert_sum_contract_fail

[Show source in test_misc.py:35](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L35)

#### Signature

```python
def test_assert_sum_contract_fail(self):
    ...
```

### MiscTest().test_assert_sum_contract_succeed

[Show source in test_misc.py:21](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L21)

#### Signature

```python
def test_assert_sum_contract_succeed(self):
    ...
```

### MiscTest().test_complex_datum_correct_vals

[Show source in test_misc.py:111](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L111)

#### Signature

```python
def test_complex_datum_correct_vals(self):
    ...
```

### MiscTest().test_datum_cast

[Show source in test_misc.py:336](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L336)

#### Signature

```python
def test_datum_cast(self):
    ...
```

### MiscTest().test_dict_datum

[Show source in test_misc.py:419](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L419)

#### Signature

```python
def test_dict_datum(self):
    ...
```

### MiscTest().test_dual_use_compile

[Show source in test_misc.py:375](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L375)

#### Signature

```python
def test_dual_use_compile(self):
    ...
```

### MiscTest().test_fib_iter

[Show source in test_misc.py:185](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L185)

#### Signature

```python
@given(n=st.integers(min_value=0, max_value=5))
def test_fib_iter(self, n):
    ...
```

### MiscTest().test_fib_rec

[Show source in test_misc.py:203](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L203)

#### Signature

```python
@given(n=st.integers(min_value=0, max_value=5))
def test_fib_rec(self, n):
    ...
```

### MiscTest().test_gift_contract_fail

[Show source in test_misc.py:273](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L273)

#### Signature

```python
def test_gift_contract_fail(self):
    ...
```

### MiscTest().test_gift_contract_succeed

[Show source in test_misc.py:240](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L240)

#### Signature

```python
def test_gift_contract_succeed(self):
    ...
```

### MiscTest().test_hello_world

[Show source in test_misc.py:138](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L138)

#### Signature

```python
def test_hello_world(self):
    ...
```

### MiscTest().test_list_comprehension_all

[Show source in test_misc.py:560](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L560)

#### Signature

```python
def test_list_comprehension_all(self):
    ...
```

### MiscTest().test_list_comprehension_even

[Show source in test_misc.py:539](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L539)

#### Signature

```python
def test_list_comprehension_even(self):
    ...
```

### MiscTest().test_list_datum_correct_vals

[Show source in test_misc.py:151](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L151)

#### Signature

```python
def test_list_datum_correct_vals(self):
    ...
```

### MiscTest().test_list_expr

[Show source in test_misc.py:477](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L477)

#### Signature

```python
def test_list_expr(self):
    ...
```

### MiscTest().test_marketplace_compile

[Show source in test_misc.py:385](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L385)

#### Signature

```python
def test_marketplace_compile(self):
    ...
```

### MiscTest().test_marketplace_compile_fail

[Show source in test_misc.py:395](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L395)

#### Signature

```python
def test_marketplace_compile_fail(self):
    ...
```

### MiscTest().test_mult_for

[Show source in test_misc.py:57](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L57)

#### Signature

```python
@given(
    a=st.integers(min_value=-10, max_value=10), b=st.integers(min_value=0, max_value=10)
)
def test_mult_for(self, a: int, b: int):
    ...
```

### MiscTest().test_mult_while

[Show source in test_misc.py:75](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L75)

#### Signature

```python
@given(
    a=st.integers(min_value=-10, max_value=10), b=st.integers(min_value=0, max_value=10)
)
def test_mult_while(self, a: int, b: int):
    ...
```

### MiscTest().test_overopt_removedeadvar

[Show source in test_misc.py:453](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L453)

#### Signature

```python
def test_overopt_removedeadvar(self):
    ...
```

### MiscTest().test_parameterized_compile

[Show source in test_misc.py:409](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L409)

#### Signature

```python
def test_parameterized_compile(self):
    ...
```

### MiscTest().test_recursion

[Show source in test_misc.py:311](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L311)

#### Signature

```python
def test_recursion(self):
    ...
```

### MiscTest().test_redefine_constr

[Show source in test_misc.py:495](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L495)

#### Signature

```python
def test_redefine_constr(self):
    ...
```

### MiscTest().test_script_context_repr_correct

[Show source in test_misc.py:221](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L221)

#### Signature

```python
@parameterized.expand(
    [
        "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87980d87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820746957f0eb57f2b11119684e611a98f373afea93473fefbb7632d579af2f6259ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff",
        "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87a9f1b000001836ac117d8ffd87a80ffd8799fd87b80d87a80ffff80a1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820797a1e1720b63621c6b185088184cb8e23af6e46b55bd83e7a91024c823a6c2affffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff",
        "d8799fd8799f9fd8799fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffd8799fd8799fd87a9f581cdbe769758f26efb21f008dc097bb194cffc622acc37fcefc5372eee3ffd87a80ffa140a1401a00989680d87a9f5820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dffd87a80ffffff809fd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a14000d87980d87a80ffd8799fd8799fd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd87a80ffa140a1401a000f4240d87980d87a80ffffa140a14000a140a1400080a0d8799fd8799fd87a9f1b000001836ac117d8ffd87a80ffd8799fd87b80d87a80ffff9f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffa1d87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffd87980a15820dfab81872ce2bbe6ee5af9bbfee4047f91c1f57db5e30da727d5fef1e7f02f4dd8799f581cdc315c289fee4484eda07038393f21dc4e572aff292d7926018725c2ffd8799f5820c17c32f6433ae22c2acaebfb796bbfaee3993ff7ebb58a2bac6b4a3bdd2f6d28ffffd87a9fd8799fd8799f582055d353acacaab6460b37ed0f0e3a1a0aabf056df4a7fa1e265d21149ccacc527ff01ffffff",
    ]
)
def test_script_context_repr_correct(self, p):
    ...
```

### MiscTest().test_showcase

[Show source in test_misc.py:168](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L168)

#### Signature

```python
def test_showcase(self):
    ...
```

### MiscTest().test_sum

[Show source in test_misc.py:93](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L93)

#### Signature

```python
@given(a=st.integers(), b=st.integers())
def test_sum(self, a: int, b: int):
    ...
```

### MiscTest().test_union_type_all_records_same_constr

[Show source in test_misc.py:601](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L601)

#### Signature

```python
@unittest.expectedFailure
def test_union_type_all_records_same_constr(self):
    ...
```

### MiscTest().test_union_type_attr_access_all_records

[Show source in test_misc.py:581](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L581)

#### Signature

```python
def test_union_type_attr_access_all_records(self):
    ...
```

### MiscTest().test_union_type_attr_access_all_records_same_constr

[Show source in test_misc.py:622](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L622)

#### Signature

```python
@unittest.expectedFailure
def test_union_type_attr_access_all_records_same_constr(self):
    ...
```

### MiscTest().test_union_type_attr_access_maximum_type

[Show source in test_misc.py:648](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L648)

#### Signature

```python
def test_union_type_attr_access_maximum_type(self):
    ...
```

### MiscTest().test_union_type_attr_anytype

[Show source in test_misc.py:668](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L668)

#### Signature

```python
def test_union_type_attr_anytype(self):
    ...
```

### MiscTest().test_wrap_into_generic_data

[Show source in test_misc.py:514](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L514)

#### Signature

```python
def test_wrap_into_generic_data(self):
    ...
```

### MiscTest().test_wrapping_contract_compile

[Show source in test_misc.py:365](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L365)

#### Signature

```python
def test_wrapping_contract_compile(self):
    ...
```



## fib

[Show source in test_misc.py:13](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/tests/test_misc.py#L13)

#### Signature

```python
def fib(n):
    ...
```