# Util

[eopsin Index](../README.md#eopsin-index) /
[Eopsin](./index.md#eopsin) /
Util

> Auto-generated documentation for [eopsin.util](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py) module.

- [Util](#util)
  - [CompilerError](#compilererror)
  - [CompilingNodeTransformer](#compilingnodetransformer)
    - [CompilingNodeTransformer().visit](#compilingnodetransformer()visit)
  - [CompilingNodeVisitor](#compilingnodevisitor)
    - [CompilingNodeVisitor().visit](#compilingnodevisitor()visit)
  - [LenImpl](#lenimpl)
    - [LenImpl().impl_from_args](#lenimpl()impl_from_args)
    - [LenImpl().type_from_args](#lenimpl()type_from_args)
  - [PythonBuiltIn](#pythonbuiltin)
  - [ReversedImpl](#reversedimpl)
    - [ReversedImpl().impl_from_args](#reversedimpl()impl_from_args)
    - [ReversedImpl().type_from_args](#reversedimpl()type_from_args)
  - [PowImpl](#powimpl)
  - [data_from_json](#data_from_json)

## CompilerError

[Show source in util.py:514](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L514)

#### Signature

```python
class CompilerError(Exception):
    def __init__(self, orig_err: Exception, node: ast.AST, compilation_step: str):
        ...
```



## CompilingNodeTransformer

[Show source in util.py:521](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L521)

#### Signature

```python
class CompilingNodeTransformer(TypedNodeTransformer):
    ...
```

### CompilingNodeTransformer().visit

[Show source in util.py:524](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L524)

#### Signature

```python
def visit(self, node):
    ...
```



## CompilingNodeVisitor

[Show source in util.py:533](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L533)

#### Signature

```python
class CompilingNodeVisitor(TypedNodeVisitor):
    ...
```

### CompilingNodeVisitor().visit

[Show source in util.py:536](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L536)

#### Signature

```python
def visit(self, node):
    ...
```



## LenImpl

[Show source in util.py:381](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L381)

#### Signature

```python
class LenImpl(PolymorphicFunction):
    ...
```

### LenImpl().impl_from_args

[Show source in util.py:391](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L391)

#### Signature

```python
def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
    ...
```

### LenImpl().type_from_args

[Show source in util.py:382](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L382)

#### Signature

```python
def type_from_args(self, args: typing.List[Type]) -> FunctionType:
    ...
```



## PythonBuiltIn

[Show source in util.py:35](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L35)

#### Attributes

- `chr` - maps an integer to a unicode code point and decodes it
  reference: https://en.wikipedia.org/wiki/UTF-8#Encoding: `plt.Lambda(['x', '_'], plt.DecodeUtf8(plt.Ite(plt.LessThanInteger(plt.Var('x'), plt.Integer(0)), plt.TraceError('ValueError: chr() arg not in range(0x110000)'), plt.Ite(plt.LessThanInteger(plt.Var('x'), plt.Integer(128)), plt.ConsByteString(plt.Var('x'), plt.ByteString(b'')), plt.Ite(plt.LessThanInteger(plt.Var('x'), plt.Integer(2048)), plt.ConsByteString(plt.AddInteger(plt.Integer(6 << 5), plt.DivideInteger(plt.Var('x'), plt.Integer(1 << 6))), plt.ConsByteString(plt.AddInteger(plt.Integer(2 << 6), plt.ModInteger(plt.Var('x'), plt.Integer(1 << 6))), plt.ByteString(b''))), plt.Ite(plt.LessThanInteger(plt.Var('x'), plt.Integer(65536)), plt.ConsByteString(plt.AddInteger(plt.Integer(14 << 4), plt.DivideInteger(plt.Var('x'), plt.Integer(1 << 12))), plt.ConsByteString(plt.AddInteger(plt.Integer(2 << 6), plt.DivideInteger(plt.ModInteger(plt.Var('x'), plt.Integer(1 << 12)), plt.Integer(1 << 6))), plt.ConsByteString(plt.AddInteger(plt.Integer(2 << 6), plt.ModInteger(plt.Var('x'), plt.Integer(1 << 6))), plt.ByteString(b'')))), plt.Ite(plt.LessThanInteger(plt.Var('x'), plt.Integer(1114112)), plt.ConsByteString(plt.AddInteger(plt.Integer(30 << 3), plt.DivideInteger(plt.Var('x'), plt.Integer(1 << 18))), plt.ConsByteString(plt.AddInteger(plt.Integer(2 << 6), plt.DivideInteger(plt.ModInteger(plt.Var('x'), plt.Integer(1 << 18)), plt.Integer(1 << 12))), plt.ConsByteString(plt.AddInteger(plt.Integer(2 << 6), plt.DivideInteger(plt.ModInteger(plt.Var('x'), plt.Integer(1 << 12)), plt.Integer(1 << 6))), plt.ConsByteString(plt.AddInteger(plt.Integer(2 << 6), plt.ModInteger(plt.Var('x'), plt.Integer(1 << 6))), plt.ByteString(b''))))), plt.TraceError('ValueError: chr() arg not in range(0x110000)'))))))))`

- `pow` - NOTE: only correctly defined for positive y: `plt.Lambda(['x', 'y', '_'], PowImpl(plt.Var('x'), plt.Var('y')))`


#### Signature

```python
class PythonBuiltIn(Enum):
    ...
```



## ReversedImpl

[Show source in util.py:411](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L411)

#### Signature

```python
class ReversedImpl(PolymorphicFunction):
    ...
```

### ReversedImpl().impl_from_args

[Show source in util.py:422](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L422)

#### Signature

```python
def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
    ...
```

### ReversedImpl().type_from_args

[Show source in util.py:412](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L412)

#### Signature

```python
def type_from_args(self, args: typing.List[Type]) -> FunctionType:
    ...
```



## PowImpl

[Show source in util.py:10](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L10)

#### Signature

```python
def PowImpl(x: plt.AST, y: plt.AST):
    ...
```



## data_from_json

[Show source in util.py:545](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/util.py#L545)

#### Signature

```python
def data_from_json(j: typing.Dict[str, typing.Any]) -> uplc.PlutusData:
    ...
```