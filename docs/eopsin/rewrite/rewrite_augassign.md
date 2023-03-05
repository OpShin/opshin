# RewriteAugAssign

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Rewrite](./index.md#rewrite) /
RewriteAugAssign

> Auto-generated documentation for [eopsin.rewrite.rewrite_augassign](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_augassign.py) module.

- [RewriteAugAssign](#rewriteaugassign)
  - [RewriteAugAssign](#rewriteaugassign-1)
    - [RewriteAugAssign().visit_AugAssign](#rewriteaugassign()visit_augassign)

## RewriteAugAssign

[Show source in rewrite_augassign.py:12](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_augassign.py#L12)

#### Signature

```python
class RewriteAugAssign(CompilingNodeTransformer):
    ...
```

### RewriteAugAssign().visit_AugAssign

[Show source in rewrite_augassign.py:15](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/rewrite/rewrite_augassign.py#L15)

#### Signature

```python
def visit_AugAssign(self, node: AugAssign) -> Assign:
    ...
```