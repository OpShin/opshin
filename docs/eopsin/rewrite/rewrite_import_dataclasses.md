# RewriteImportDataclasses

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Rewrite](./index.md#rewrite) /
RewriteImportDataclasses

> Auto-generated documentation for [eopsin.rewrite.rewrite_import_dataclasses](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_import_dataclasses.py) module.

- [RewriteImportDataclasses](#rewriteimportdataclasses)
  - [RewriteImportDataclasses](#rewriteimportdataclasses-1)
    - [RewriteImportDataclasses().visit_ClassDef](#rewriteimportdataclasses()visit_classdef)
    - [RewriteImportDataclasses().visit_ImportFrom](#rewriteimportdataclasses()visit_importfrom)

## RewriteImportDataclasses

[Show source in rewrite_import_dataclasses.py:11](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_import_dataclasses.py#L11)

#### Signature

```python
class RewriteImportDataclasses(CompilingNodeTransformer):
    ...
```

### RewriteImportDataclasses().visit_ClassDef

[Show source in rewrite_import_dataclasses.py:32](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_import_dataclasses.py#L32)

#### Signature

```python
def visit_ClassDef(self, node: ClassDef) -> ClassDef:
    ...
```

### RewriteImportDataclasses().visit_ImportFrom

[Show source in rewrite_import_dataclasses.py:16](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_import_dataclasses.py#L16)

#### Signature

```python
def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
    ...
```