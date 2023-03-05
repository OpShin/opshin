# RewriteImportTyping

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Rewrite](./index.md#rewrite) /
RewriteImportTyping

> Auto-generated documentation for [eopsin.rewrite.rewrite_import_typing](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_import_typing.py) module.

- [RewriteImportTyping](#rewriteimporttyping)
  - [RewriteImportTyping](#rewriteimporttyping-1)
    - [RewriteImportTyping().visit_ClassDef](#rewriteimporttyping()visit_classdef)
    - [RewriteImportTyping().visit_ImportFrom](#rewriteimporttyping()visit_importfrom)

## RewriteImportTyping

[Show source in rewrite_import_typing.py:11](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_import_typing.py#L11)

#### Signature

```python
class RewriteImportTyping(CompilingNodeTransformer):
    ...
```

### RewriteImportTyping().visit_ClassDef

[Show source in rewrite_import_typing.py:32](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_import_typing.py#L32)

#### Signature

```python
def visit_ClassDef(self, node: ClassDef) -> ClassDef:
    ...
```

### RewriteImportTyping().visit_ImportFrom

[Show source in rewrite_import_typing.py:16](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_import_typing.py#L16)

#### Signature

```python
def visit_ImportFrom(self, node: ImportFrom) -> Optional[ImportFrom]:
    ...
```