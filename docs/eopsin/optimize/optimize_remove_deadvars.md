# OptimizeRemoveDeadvars

[eopsin Index](../../README.md#eopsin-index) /
[Eopsin](../index.md#eopsin) /
[Optimize](./index.md#optimize) /
OptimizeRemoveDeadvars

> Auto-generated documentation for [eopsin.optimize.optimize_remove_deadvars](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py) module.

- [OptimizeRemoveDeadvars](#optimizeremovedeadvars)
  - [NameLoadCollector](#nameloadcollector)
    - [NameLoadCollector().visit_ClassDef](#nameloadcollector()visit_classdef)
    - [NameLoadCollector().visit_FunctionDef](#nameloadcollector()visit_functiondef)
    - [NameLoadCollector().visit_Name](#nameloadcollector()visit_name)
  - [OptimizeRemoveDeadvars](#optimizeremovedeadvars-1)
    - [OptimizeRemoveDeadvars().enter_scope](#optimizeremovedeadvars()enter_scope)
    - [OptimizeRemoveDeadvars().exit_scope](#optimizeremovedeadvars()exit_scope)
    - [OptimizeRemoveDeadvars().guaranteed](#optimizeremovedeadvars()guaranteed)
    - [OptimizeRemoveDeadvars().set_guaranteed](#optimizeremovedeadvars()set_guaranteed)
    - [OptimizeRemoveDeadvars().visit_AnnAssign](#optimizeremovedeadvars()visit_annassign)
    - [OptimizeRemoveDeadvars().visit_Assign](#optimizeremovedeadvars()visit_assign)
    - [OptimizeRemoveDeadvars().visit_ClassDef](#optimizeremovedeadvars()visit_classdef)
    - [OptimizeRemoveDeadvars().visit_For](#optimizeremovedeadvars()visit_for)
    - [OptimizeRemoveDeadvars().visit_FunctionDef](#optimizeremovedeadvars()visit_functiondef)
    - [OptimizeRemoveDeadvars().visit_If](#optimizeremovedeadvars()visit_if)
    - [OptimizeRemoveDeadvars().visit_Module](#optimizeremovedeadvars()visit_module)
    - [OptimizeRemoveDeadvars().visit_While](#optimizeremovedeadvars()visit_while)
  - [SafeOperationVisitor](#safeoperationvisitor)
    - [SafeOperationVisitor().generic_visit](#safeoperationvisitor()generic_visit)
    - [SafeOperationVisitor().visit_Constant](#safeoperationvisitor()visit_constant)
    - [SafeOperationVisitor().visit_Lambda](#safeoperationvisitor()visit_lambda)
    - [SafeOperationVisitor().visit_Name](#safeoperationvisitor()visit_name)
    - [SafeOperationVisitor().visit_RawPlutoExpr](#safeoperationvisitor()visit_rawplutoexpr)

## NameLoadCollector

[Show source in optimize_remove_deadvars.py:13](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L13)

#### Signature

```python
class NameLoadCollector(CompilingNodeVisitor):
    def __init__(self):
        ...
```

### NameLoadCollector().visit_ClassDef

[Show source in optimize_remove_deadvars.py:23](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L23)

#### Signature

```python
def visit_ClassDef(self, node: ClassDef):
    ...
```

### NameLoadCollector().visit_FunctionDef

[Show source in optimize_remove_deadvars.py:27](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L27)

#### Signature

```python
def visit_FunctionDef(self, node: FunctionDef):
    ...
```

### NameLoadCollector().visit_Name

[Show source in optimize_remove_deadvars.py:19](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L19)

#### Signature

```python
def visit_Name(self, node: Name) -> None:
    ...
```



## OptimizeRemoveDeadvars

[Show source in optimize_remove_deadvars.py:59](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L59)

#### Attributes

- `guaranteed_avail_names` - names that are guaranteed to be available to the current node
  this acts differently to the type inferencer! in particular, ite/while/for all produce their own scope: `[list(INITIAL_SCOPE.keys())]`


#### Signature

```python
class OptimizeRemoveDeadvars(CompilingNodeTransformer):
    ...
```

### OptimizeRemoveDeadvars().enter_scope

[Show source in optimize_remove_deadvars.py:74](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L74)

#### Signature

```python
def enter_scope(self):
    ...
```

### OptimizeRemoveDeadvars().exit_scope

[Show source in optimize_remove_deadvars.py:77](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L77)

#### Signature

```python
def exit_scope(self):
    ...
```

### OptimizeRemoveDeadvars().guaranteed

[Show source in optimize_remove_deadvars.py:67](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L67)

#### Signature

```python
def guaranteed(self, name: str) -> bool:
    ...
```

### OptimizeRemoveDeadvars().set_guaranteed

[Show source in optimize_remove_deadvars.py:80](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L80)

#### Signature

```python
def set_guaranteed(self, name: str):
    ...
```

### OptimizeRemoveDeadvars().visit_AnnAssign

[Show source in optimize_remove_deadvars.py:148](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L148)

#### Signature

```python
def visit_AnnAssign(self, node: AnnAssign):
    ...
```

### OptimizeRemoveDeadvars().visit_Assign

[Show source in optimize_remove_deadvars.py:131](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L131)

#### Signature

```python
def visit_Assign(self, node: Assign):
    ...
```

### OptimizeRemoveDeadvars().visit_ClassDef

[Show source in optimize_remove_deadvars.py:163](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L163)

#### Signature

```python
def visit_ClassDef(self, node: ClassDef):
    ...
```

### OptimizeRemoveDeadvars().visit_For

[Show source in optimize_remove_deadvars.py:121](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L121)

#### Signature

```python
def visit_For(self, node: For):
    ...
```

### OptimizeRemoveDeadvars().visit_FunctionDef

[Show source in optimize_remove_deadvars.py:169](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L169)

#### Signature

```python
def visit_FunctionDef(self, node: FunctionDef):
    ...
```

### OptimizeRemoveDeadvars().visit_If

[Show source in optimize_remove_deadvars.py:103](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L103)

#### Signature

```python
def visit_If(self, node: If):
    ...
```

### OptimizeRemoveDeadvars().visit_Module

[Show source in optimize_remove_deadvars.py:83](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L83)

#### Signature

```python
def visit_Module(self, node: Module) -> Module:
    ...
```

### OptimizeRemoveDeadvars().visit_While

[Show source in optimize_remove_deadvars.py:112](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L112)

#### Signature

```python
def visit_While(self, node: While):
    ...
```



## SafeOperationVisitor

[Show source in optimize_remove_deadvars.py:33](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L33)

#### Signature

```python
class SafeOperationVisitor(CompilingNodeVisitor):
    def __init__(self, guaranteed_names):
        ...
```

### SafeOperationVisitor().generic_visit

[Show source in optimize_remove_deadvars.py:39](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L39)

#### Signature

```python
def generic_visit(self, node: AST) -> bool:
    ...
```

### SafeOperationVisitor().visit_Constant

[Show source in optimize_remove_deadvars.py:47](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L47)

#### Signature

```python
def visit_Constant(self, node: Constant) -> bool:
    ...
```

### SafeOperationVisitor().visit_Lambda

[Show source in optimize_remove_deadvars.py:43](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L43)

#### Signature

```python
def visit_Lambda(self, node: Lambda) -> bool:
    ...
```

### SafeOperationVisitor().visit_Name

[Show source in optimize_remove_deadvars.py:55](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L55)

#### Signature

```python
def visit_Name(self, node: Name) -> bool:
    ...
```

### SafeOperationVisitor().visit_RawPlutoExpr

[Show source in optimize_remove_deadvars.py:51](https://github.com/ImperatorLang/eopsin/blob/master/eopsin/optimize/optimize_remove_deadvars.py#L51)

#### Signature

```python
def visit_RawPlutoExpr(self, node) -> bool:
    ...
```