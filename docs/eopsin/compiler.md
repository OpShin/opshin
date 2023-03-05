# Compiler

[eopsin Index](../README.md#eopsin-index) /
[Eopsin](./index.md#eopsin) /
Compiler

> Auto-generated documentation for [eopsin.compiler](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py) module.

- [Compiler](#compiler)
  - [UPLCCompiler](#uplccompiler)
    - [UPLCCompiler().generic_visit](#uplccompiler()generic_visit)
    - [UPLCCompiler().visit_AnnAssign](#uplccompiler()visit_annassign)
    - [UPLCCompiler().visit_Assert](#uplccompiler()visit_assert)
    - [UPLCCompiler().visit_Assign](#uplccompiler()visit_assign)
    - [UPLCCompiler().visit_Attribute](#uplccompiler()visit_attribute)
    - [UPLCCompiler().visit_BinOp](#uplccompiler()visit_binop)
    - [UPLCCompiler().visit_BoolOp](#uplccompiler()visit_boolop)
    - [UPLCCompiler().visit_Call](#uplccompiler()visit_call)
    - [UPLCCompiler().visit_ClassDef](#uplccompiler()visit_classdef)
    - [UPLCCompiler().visit_Compare](#uplccompiler()visit_compare)
    - [UPLCCompiler().visit_Constant](#uplccompiler()visit_constant)
    - [UPLCCompiler().visit_Dict](#uplccompiler()visit_dict)
    - [UPLCCompiler().visit_Expr](#uplccompiler()visit_expr)
    - [UPLCCompiler().visit_For](#uplccompiler()visit_for)
    - [UPLCCompiler().visit_FunctionDef](#uplccompiler()visit_functiondef)
    - [UPLCCompiler().visit_If](#uplccompiler()visit_if)
    - [UPLCCompiler().visit_IfExp](#uplccompiler()visit_ifexp)
    - [UPLCCompiler().visit_List](#uplccompiler()visit_list)
    - [UPLCCompiler().visit_ListComp](#uplccompiler()visit_listcomp)
    - [UPLCCompiler().visit_Module](#uplccompiler()visit_module)
    - [UPLCCompiler().visit_Name](#uplccompiler()visit_name)
    - [UPLCCompiler().visit_NoneType](#uplccompiler()visit_nonetype)
    - [UPLCCompiler().visit_Pass](#uplccompiler()visit_pass)
    - [UPLCCompiler().visit_RawPlutoExpr](#uplccompiler()visit_rawplutoexpr)
    - [UPLCCompiler().visit_Return](#uplccompiler()visit_return)
    - [UPLCCompiler().visit_Subscript](#uplccompiler()visit_subscript)
    - [UPLCCompiler().visit_Tuple](#uplccompiler()visit_tuple)
    - [UPLCCompiler().visit_UnaryOp](#uplccompiler()visit_unaryop)
    - [UPLCCompiler().visit_While](#uplccompiler()visit_while)
    - [UPLCCompiler().visit_sequence](#uplccompiler()visit_sequence)
  - [compile](#compile)
  - [extend_statemonad](#extend_statemonad)
  - [wrap_validator_double_function](#wrap_validator_double_function)

## UPLCCompiler

[Show source in compiler.py:138](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L138)

Expects a TypedAST and returns UPLC/Pluto like code

#### Signature

```python
class UPLCCompiler(CompilingNodeTransformer):
    def __init__(self, force_three_params=False):
        ...
```

### UPLCCompiler().generic_visit

[Show source in compiler.py:838](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L838)

#### Signature

```python
def generic_visit(self, node: AST) -> plt.AST:
    ...
```

### UPLCCompiler().visit_AnnAssign

[Show source in compiler.py:328](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L328)

#### Signature

```python
def visit_AnnAssign(self, node: AnnAssign) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Assert

[Show source in compiler.py:728](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L728)

#### Signature

```python
def visit_Assert(self, node: TypedAssert) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Assign

[Show source in compiler.py:309](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L309)

#### Signature

```python
def visit_Assign(self, node: TypedAssign) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Attribute

[Show source in compiler.py:718](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L718)

#### Signature

```python
def visit_Attribute(self, node: TypedAttribute) -> plt.AST:
    ...
```

### UPLCCompiler().visit_BinOp

[Show source in compiler.py:155](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L155)

#### Signature

```python
def visit_BinOp(self, node: TypedBinOp) -> plt.AST:
    ...
```

### UPLCCompiler().visit_BoolOp

[Show source in compiler.py:177](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L177)

#### Signature

```python
def visit_BoolOp(self, node: TypedBoolOp) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Call

[Show source in compiler.py:382](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L382)

#### Signature

```python
def visit_Call(self, node: TypedCall) -> plt.AST:
    ...
```

### UPLCCompiler().visit_ClassDef

[Show source in compiler.py:708](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L708)

#### Signature

```python
def visit_ClassDef(self, node: TypedClassDef) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Compare

[Show source in compiler.py:203](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L203)

#### Signature

```python
def visit_Compare(self, node: TypedCompare) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Constant

[Show source in compiler.py:298](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L298)

#### Signature

```python
def visit_Constant(self, node: TypedConstant) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Dict

[Show source in compiler.py:756](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L756)

#### Signature

```python
def visit_Dict(self, node: TypedDict) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Expr

[Show source in compiler.py:370](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L370)

#### Signature

```python
def visit_Expr(self, node: TypedExpr) -> plt.AST:
    ...
```

### UPLCCompiler().visit_For

[Show source in compiler.py:483](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L483)

#### Signature

```python
def visit_For(self, node: TypedFor) -> plt.AST:
    ...
```

### UPLCCompiler().visit_FunctionDef

[Show source in compiler.py:412](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L412)

#### Signature

```python
def visit_FunctionDef(self, node: TypedFunctionDef) -> plt.AST:
    ...
```

### UPLCCompiler().visit_If

[Show source in compiler.py:516](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L516)

#### Signature

```python
def visit_If(self, node: TypedIf) -> plt.AST:
    ...
```

### UPLCCompiler().visit_IfExp

[Show source in compiler.py:776](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L776)

#### Signature

```python
def visit_IfExp(self, node: TypedIfExp) -> plt.AST:
    ...
```

### UPLCCompiler().visit_List

[Show source in compiler.py:748](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L748)

#### Signature

```python
def visit_List(self, node: TypedList) -> plt.AST:
    ...
```

### UPLCCompiler().visit_ListComp

[Show source in compiler.py:786](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L786)

#### Signature

```python
def visit_ListComp(self, node: TypedListComp) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Module

[Show source in compiler.py:218](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L218)

#### Signature

```python
def visit_Module(self, node: TypedModule) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Name

[Show source in compiler.py:351](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L351)

#### Signature

```python
def visit_Name(self, node: TypedName) -> plt.AST:
    ...
```

### UPLCCompiler().visit_NoneType

[Show source in compiler.py:306](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L306)

#### Signature

```python
def visit_NoneType(self, _: typing.Optional[typing.Any]) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Pass

[Show source in compiler.py:531](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L531)

#### Signature

```python
def visit_Pass(self, node: TypedPass) -> plt.AST:
    ...
```

### UPLCCompiler().visit_RawPlutoExpr

[Show source in compiler.py:745](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L745)

#### Signature

```python
def visit_RawPlutoExpr(self, node: RawPlutoExpr) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Return

[Show source in compiler.py:526](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L526)

#### Signature

```python
def visit_Return(self, node: TypedReturn) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Subscript

[Show source in compiler.py:534](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L534)

#### Signature

```python
def visit_Subscript(self, node: TypedSubscript) -> plt.AST:
    ...
```

### UPLCCompiler().visit_Tuple

[Show source in compiler.py:700](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L700)

#### Signature

```python
def visit_Tuple(self, node: TypedTuple) -> plt.AST:
    ...
```

### UPLCCompiler().visit_UnaryOp

[Show source in compiler.py:191](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L191)

#### Signature

```python
def visit_UnaryOp(self, node: TypedUnaryOp) -> plt.AST:
    ...
```

### UPLCCompiler().visit_While

[Show source in compiler.py:450](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L450)

#### Signature

```python
def visit_While(self, node: TypedWhile) -> plt.AST:
    ...
```

### UPLCCompiler().visit_sequence

[Show source in compiler.py:148](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L148)

#### Signature

```python
def visit_sequence(self, node_seq: typing.List[typedstmt]) -> plt.AST:
    ...
```



## compile

[Show source in compiler.py:842](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L842)

#### Signature

```python
def compile(prog: AST, force_three_params=False):
    ...
```



## extend_statemonad

[Show source in compiler.py:116](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L116)

Ensures that the argument is fully evaluated before being passed into the monad (like in imperative languages)

#### Signature

```python
def extend_statemonad(
    names: typing.List[str],
    values: typing.List[plt.AST],
    old_statemonad: plt.FunctionalMap,
):
    ...
```



## wrap_validator_double_function

[Show source in compiler.py:87](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/compiler.py#L87)

Wraps the validator function to enable a double function as minting script

pass_through defines how many parameters x would normally take and should be passed through to x

#### Signature

```python
def wrap_validator_double_function(x: plt.AST, pass_through: int = 0):
    ...
```