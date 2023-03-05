# OptimizeVarlen

[Eopsin-lang Index](../../README.md#eopsin-lang-index) /
[Eopsin](../index.md#eopsin) /
[Optimize](./index.md#optimize) /
OptimizeVarlen

> Auto-generated documentation for [eopsin.optimize.optimize_varlen](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py) module.

- [OptimizeVarlen](#optimizevarlen)
  - [NameCollector](#namecollector)
    - [NameCollector().visit_ClassDef](#namecollector()visit_classdef)
    - [NameCollector().visit_FunctionDef](#namecollector()visit_functiondef)
    - [NameCollector().visit_Name](#namecollector()visit_name)
  - [OptimizeVarlen](#optimizevarlen-1)
    - [OptimizeVarlen().visit_ClassDef](#optimizevarlen()visit_classdef)
    - [OptimizeVarlen().visit_FunctionDef](#optimizevarlen()visit_functiondef)
    - [OptimizeVarlen().visit_Module](#optimizevarlen()visit_module)
    - [OptimizeVarlen().visit_Name](#optimizevarlen()visit_name)
  - [bs_from_int](#bs_from_int)

## NameCollector

[Show source in optimize_varlen.py:12](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L12)

#### Signature

```python
class NameCollector(CompilingNodeVisitor):
    def __init__(self):
        ...
```

### NameCollector().visit_ClassDef

[Show source in optimize_varlen.py:21](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L21)

#### Signature

```python
def visit_ClassDef(self, node: ClassDef):
    ...
```

### NameCollector().visit_FunctionDef

[Show source in optimize_varlen.py:25](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L25)

#### Signature

```python
def visit_FunctionDef(self, node: FunctionDef):
    ...
```

### NameCollector().visit_Name

[Show source in optimize_varlen.py:18](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L18)

#### Signature

```python
def visit_Name(self, node: Name) -> None:
    ...
```



## OptimizeVarlen

[Show source in optimize_varlen.py:41](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L41)

#### Signature

```python
class OptimizeVarlen(CompilingNodeTransformer):
    ...
```

### OptimizeVarlen().visit_ClassDef

[Show source in optimize_varlen.py:66](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L66)

#### Signature

```python
def visit_ClassDef(self, node: ClassDef) -> ClassDef:
    ...
```

### OptimizeVarlen().visit_FunctionDef

[Show source in optimize_varlen.py:73](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L73)

#### Signature

```python
def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
    ...
```

### OptimizeVarlen().visit_Module

[Show source in optimize_varlen.py:46](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L46)

#### Signature

```python
def visit_Module(self, node: Module) -> Module:
    ...
```

### OptimizeVarlen().visit_Name

[Show source in optimize_varlen.py:60](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L60)

#### Signature

```python
def visit_Name(self, node: Name) -> Name:
    ...
```



## bs_from_int

[Show source in optimize_varlen.py:34](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/optimize/optimize_varlen.py#L34)

#### Signature

```python
def bs_from_int(i: int):
    ...
```