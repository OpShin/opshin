# RewriteImportHashlib

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Rewrite](./index.md#rewrite) /
RewriteImportHashlib

> Auto-generated documentation for [eopsin.rewrite.rewrite_import_hashlib](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_import_hashlib.py) module.

- [RewriteImportHashlib](#rewriteimporthashlib)
  - [HashType](#hashtype)
    - [HashType().attribute](#hashtype()attribute)
    - [HashType().attribute_type](#hashtype()attribute_type)
  - [PythonHashlib](#pythonhashlib)
  - [RewriteImportHashlib](#rewriteimporthashlib-1)
    - [RewriteImportHashlib().visit_ImportFrom](#rewriteimporthashlib()visit_importfrom)

## HashType

[Show source in rewrite_import_hashlib.py:13](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_import_hashlib.py#L13)

A pseudo class that is the result of python hash functions that need a 'digest' call

#### Signature

```python
class HashType(ClassType):
    ...
```

### HashType().attribute

[Show source in rewrite_import_hashlib.py:21](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_import_hashlib.py#L21)

#### Signature

```python
def attribute(self, attr) -> plt.AST:
    ...
```

### HashType().attribute_type

[Show source in rewrite_import_hashlib.py:16](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_import_hashlib.py#L16)

#### Signature

```python
def attribute_type(self, attr) -> "Type":
    ...
```



## PythonHashlib

[Show source in rewrite_import_hashlib.py:30](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_import_hashlib.py#L30)

#### Signature

```python
class PythonHashlib(Enum):
    ...
```



## RewriteImportHashlib

[Show source in rewrite_import_hashlib.py:58](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_import_hashlib.py#L58)

#### Signature

```python
class RewriteImportHashlib(CompilingNodeTransformer):
    ...
```

### RewriteImportHashlib().visit_ImportFrom

[Show source in rewrite_import_hashlib.py:63](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_import_hashlib.py#L63)

#### Signature

```python
def visit_ImportFrom(self, node: ImportFrom) -> typing.List[AST]:
    ...
```