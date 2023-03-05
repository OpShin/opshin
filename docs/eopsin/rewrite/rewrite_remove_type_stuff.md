# RewriteRemoveTypeStuff

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Rewrite](./index.md#rewrite) /
RewriteRemoveTypeStuff

> Auto-generated documentation for [eopsin.rewrite.rewrite_remove_type_stuff](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_remove_type_stuff.py) module.

- [RewriteRemoveTypeStuff](#rewriteremovetypestuff)
  - [RewriteRemoveTypeStuff](#rewriteremovetypestuff-1)
    - [RewriteRemoveTypeStuff().visit_Assign](#rewriteremovetypestuff()visit_assign)

## RewriteRemoveTypeStuff

[Show source in rewrite_remove_type_stuff.py:11](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_remove_type_stuff.py#L11)

#### Signature

```python
class RewriteRemoveTypeStuff(CompilingNodeTransformer):
    ...
```

### RewriteRemoveTypeStuff().visit_Assign

[Show source in rewrite_remove_type_stuff.py:14](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/rewrite/rewrite_remove_type_stuff.py#L14)

#### Signature

```python
def visit_Assign(self, node: TypedAssign) -> Optional[TypedAssign]:
    ...
```