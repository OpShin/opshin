# Type Inference

[eopsin Index](../README.md#eopsin-index) /
[Eopsin](./index.md#eopsin) /
Type Inference

> Auto-generated documentation for [eopsin.type_inference](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py) module.

- [Type Inference](#type-inference)
  - [AggressiveTypeInferencer](#aggressivetypeinferencer)
    - [AggressiveTypeInferencer().enter_scope](#aggressivetypeinferencer()enter_scope)
    - [AggressiveTypeInferencer().exit_scope](#aggressivetypeinferencer()exit_scope)
    - [AggressiveTypeInferencer().generic_visit](#aggressivetypeinferencer()generic_visit)
    - [AggressiveTypeInferencer().set_variable_type](#aggressivetypeinferencer()set_variable_type)
    - [AggressiveTypeInferencer().type_from_annotation](#aggressivetypeinferencer()type_from_annotation)
    - [AggressiveTypeInferencer().variable_type](#aggressivetypeinferencer()variable_type)
    - [AggressiveTypeInferencer().visit_AnnAssign](#aggressivetypeinferencer()visit_annassign)
    - [AggressiveTypeInferencer().visit_Assert](#aggressivetypeinferencer()visit_assert)
    - [AggressiveTypeInferencer().visit_Assign](#aggressivetypeinferencer()visit_assign)
    - [AggressiveTypeInferencer().visit_Attribute](#aggressivetypeinferencer()visit_attribute)
    - [AggressiveTypeInferencer().visit_BinOp](#aggressivetypeinferencer()visit_binop)
    - [AggressiveTypeInferencer().visit_BoolOp](#aggressivetypeinferencer()visit_boolop)
    - [AggressiveTypeInferencer().visit_Call](#aggressivetypeinferencer()visit_call)
    - [AggressiveTypeInferencer().visit_ClassDef](#aggressivetypeinferencer()visit_classdef)
    - [AggressiveTypeInferencer().visit_Compare](#aggressivetypeinferencer()visit_compare)
    - [AggressiveTypeInferencer().visit_Constant](#aggressivetypeinferencer()visit_constant)
    - [AggressiveTypeInferencer().visit_Dict](#aggressivetypeinferencer()visit_dict)
    - [AggressiveTypeInferencer().visit_Expr](#aggressivetypeinferencer()visit_expr)
    - [AggressiveTypeInferencer().visit_For](#aggressivetypeinferencer()visit_for)
    - [AggressiveTypeInferencer().visit_FunctionDef](#aggressivetypeinferencer()visit_functiondef)
    - [AggressiveTypeInferencer().visit_If](#aggressivetypeinferencer()visit_if)
    - [AggressiveTypeInferencer().visit_IfExp](#aggressivetypeinferencer()visit_ifexp)
    - [AggressiveTypeInferencer().visit_List](#aggressivetypeinferencer()visit_list)
    - [AggressiveTypeInferencer().visit_ListComp](#aggressivetypeinferencer()visit_listcomp)
    - [AggressiveTypeInferencer().visit_Module](#aggressivetypeinferencer()visit_module)
    - [AggressiveTypeInferencer().visit_Name](#aggressivetypeinferencer()visit_name)
    - [AggressiveTypeInferencer().visit_Pass](#aggressivetypeinferencer()visit_pass)
    - [AggressiveTypeInferencer().visit_RawPlutoExpr](#aggressivetypeinferencer()visit_rawplutoexpr)
    - [AggressiveTypeInferencer().visit_Return](#aggressivetypeinferencer()visit_return)
    - [AggressiveTypeInferencer().visit_Subscript](#aggressivetypeinferencer()visit_subscript)
    - [AggressiveTypeInferencer().visit_Tuple](#aggressivetypeinferencer()visit_tuple)
    - [AggressiveTypeInferencer().visit_UnaryOp](#aggressivetypeinferencer()visit_unaryop)
    - [AggressiveTypeInferencer().visit_While](#aggressivetypeinferencer()visit_while)
    - [AggressiveTypeInferencer().visit_arg](#aggressivetypeinferencer()visit_arg)
    - [AggressiveTypeInferencer().visit_arguments](#aggressivetypeinferencer()visit_arguments)
    - [AggressiveTypeInferencer().visit_comprehension](#aggressivetypeinferencer()visit_comprehension)
  - [RecordReader](#recordreader)
    - [RecordReader.extract](#recordreaderextract)
    - [RecordReader().generic_visit](#recordreader()generic_visit)
    - [RecordReader().visit_AnnAssign](#recordreader()visit_annassign)
    - [RecordReader().visit_Assign](#recordreader()visit_assign)
    - [RecordReader().visit_ClassDef](#recordreader()visit_classdef)
    - [RecordReader().visit_Expr](#recordreader()visit_expr)
    - [RecordReader().visit_Pass](#recordreader()visit_pass)
  - [typed_ast](#typed_ast)

## AggressiveTypeInferencer

[Show source in type_inference.py:45](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L45)

#### Attributes

- `scopes` - A stack of dictionaries for storing scoped knowledge of variable types: `[INITIAL_SCOPE]`


#### Signature

```python
class AggressiveTypeInferencer(CompilingNodeTransformer):
    ...
```

### AggressiveTypeInferencer().enter_scope

[Show source in type_inference.py:59](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L59)

#### Signature

```python
def enter_scope(self):
    ...
```

### AggressiveTypeInferencer().exit_scope

[Show source in type_inference.py:62](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L62)

#### Signature

```python
def exit_scope(self):
    ...
```

### AggressiveTypeInferencer().generic_visit

[Show source in type_inference.py:610](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L610)

#### Signature

```python
def generic_visit(self, node: AST) -> TypedAST:
    ...
```

### AggressiveTypeInferencer().set_variable_type

[Show source in type_inference.py:65](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L65)

#### Signature

```python
def set_variable_type(self, name: str, typ: Type, force=False):
    ...
```

### AggressiveTypeInferencer().type_from_annotation

[Show source in type_inference.py:72](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L72)

#### Signature

```python
def type_from_annotation(self, ann: expr):
    ...
```

### AggressiveTypeInferencer().variable_type

[Show source in type_inference.py:52](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L52)

#### Signature

```python
def variable_type(self, name: str) -> Type:
    ...
```

### AggressiveTypeInferencer().visit_AnnAssign

[Show source in type_inference.py:206](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L206)

#### Signature

```python
def visit_AnnAssign(self, node: AnnAssign) -> TypedAnnAssign:
    ...
```

### AggressiveTypeInferencer().visit_Assert

[Show source in type_inference.py:537](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L537)

#### Signature

```python
def visit_Assert(self, node: Assert) -> TypedAssert:
    ...
```

### AggressiveTypeInferencer().visit_Assign

[Show source in type_inference.py:194](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L194)

#### Signature

```python
def visit_Assign(self, node: Assign) -> TypedAssign:
    ...
```

### AggressiveTypeInferencer().visit_Attribute

[Show source in type_inference.py:529](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L529)

#### Signature

```python
def visit_Attribute(self, node: Attribute) -> TypedAttribute:
    ...
```

### AggressiveTypeInferencer().visit_BinOp

[Show source in type_inference.py:380](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L380)

#### Signature

```python
def visit_BinOp(self, node: BinOp) -> TypedBinOp:
    ...
```

### AggressiveTypeInferencer().visit_BoolOp

[Show source in type_inference.py:391](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L391)

#### Signature

```python
def visit_BoolOp(self, node: BoolOp) -> TypedBoolOp:
    ...
```

### AggressiveTypeInferencer().visit_Call

[Show source in type_inference.py:486](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L486)

#### Signature

```python
def visit_Call(self, node: Call) -> TypedCall:
    ...
```

### AggressiveTypeInferencer().visit_ClassDef

[Show source in type_inference.py:144](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L144)

#### Signature

```python
def visit_ClassDef(self, node: ClassDef) -> TypedClassDef:
    ...
```

### AggressiveTypeInferencer().visit_Compare

[Show source in type_inference.py:318](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L318)

#### Signature

```python
def visit_Compare(self, node: Compare) -> TypedCompare:
    ...
```

### AggressiveTypeInferencer().visit_Constant

[Show source in type_inference.py:152](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L152)

#### Signature

```python
def visit_Constant(self, node: Constant) -> TypedConstant:
    ...
```

### AggressiveTypeInferencer().visit_Dict

[Show source in type_inference.py:181](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L181)

#### Signature

```python
def visit_Dict(self, node: Dict) -> TypedDict:
    ...
```

### AggressiveTypeInferencer().visit_Expr

[Show source in type_inference.py:375](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L375)

#### Signature

```python
def visit_Expr(self, node: Expr) -> TypedExpr:
    ...
```

### AggressiveTypeInferencer().visit_For

[Show source in type_inference.py:282](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L282)

#### Signature

```python
def visit_For(self, node: For) -> TypedFor:
    ...
```

### AggressiveTypeInferencer().visit_FunctionDef

[Show source in type_inference.py:341](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L341)

#### Signature

```python
def visit_FunctionDef(self, node: FunctionDef) -> TypedFunctionDef:
    ...
```

### AggressiveTypeInferencer().visit_If

[Show source in type_inference.py:222](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L222)

#### Signature

```python
def visit_If(self, node: If) -> TypedIf:
    ...
```

### AggressiveTypeInferencer().visit_IfExp

[Show source in type_inference.py:554](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L554)

#### Signature

```python
def visit_IfExp(self, node: IfExp) -> TypedIfExp:
    ...
```

### AggressiveTypeInferencer().visit_List

[Show source in type_inference.py:171](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L171)

#### Signature

```python
def visit_List(self, node: List) -> TypedList:
    ...
```

### AggressiveTypeInferencer().visit_ListComp

[Show source in type_inference.py:598](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L598)

#### Signature

```python
def visit_ListComp(self, node: ListComp) -> TypedListComp:
    ...
```

### AggressiveTypeInferencer().visit_Module

[Show source in type_inference.py:368](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L368)

#### Signature

```python
def visit_Module(self, node: Module) -> TypedModule:
    ...
```

### AggressiveTypeInferencer().visit_Name

[Show source in type_inference.py:312](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L312)

#### Signature

```python
def visit_Name(self, node: Name) -> TypedName:
    ...
```

### AggressiveTypeInferencer().visit_Pass

[Show source in type_inference.py:519](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L519)

#### Signature

```python
def visit_Pass(self, node: Pass) -> TypedPass:
    ...
```

### AggressiveTypeInferencer().visit_RawPlutoExpr

[Show source in type_inference.py:550](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L550)

#### Signature

```python
def visit_RawPlutoExpr(self, node: RawPlutoExpr) -> RawPlutoExpr:
    ...
```

### AggressiveTypeInferencer().visit_Return

[Show source in type_inference.py:523](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L523)

#### Signature

```python
def visit_Return(self, node: Return) -> TypedReturn:
    ...
```

### AggressiveTypeInferencer().visit_Subscript

[Show source in type_inference.py:406](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L406)

#### Signature

```python
def visit_Subscript(self, node: Subscript) -> TypedSubscript:
    ...
```

### AggressiveTypeInferencer().visit_Tuple

[Show source in type_inference.py:165](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L165)

#### Signature

```python
def visit_Tuple(self, node: Tuple) -> TypedTuple:
    ...
```

### AggressiveTypeInferencer().visit_UnaryOp

[Show source in type_inference.py:400](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L400)

#### Signature

```python
def visit_UnaryOp(self, node: UnaryOp) -> TypedUnaryOp:
    ...
```

### AggressiveTypeInferencer().visit_While

[Show source in type_inference.py:272](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L272)

#### Signature

```python
def visit_While(self, node: While) -> TypedWhile:
    ...
```

### AggressiveTypeInferencer().visit_arg

[Show source in type_inference.py:326](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L326)

#### Signature

```python
def visit_arg(self, node: arg) -> typedarg:
    ...
```

### AggressiveTypeInferencer().visit_arguments

[Show source in type_inference.py:332](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L332)

#### Signature

```python
def visit_arguments(self, node: arguments) -> typedarguments:
    ...
```

### AggressiveTypeInferencer().visit_comprehension

[Show source in type_inference.py:570](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L570)

#### Signature

```python
def visit_comprehension(self, g: comprehension) -> typedcomprehension:
    ...
```



## RecordReader

[Show source in type_inference.py:616](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L616)

#### Signature

```python
class RecordReader(NodeVisitor):
    def __init__(self, type_inferencer: AggressiveTypeInferencer):
        ...
```

#### See also

- [AggressiveTypeInferencer](#aggressivetypeinferencer)

### RecordReader.extract

[Show source in type_inference.py:627](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L627)

#### Signature

```python
@classmethod
def extract(cls, c: ClassDef, type_inferencer: AggressiveTypeInferencer) -> Record:
    ...
```

#### See also

- [AggressiveTypeInferencer](#aggressivetypeinferencer)

### RecordReader().generic_visit

[Show source in type_inference.py:690](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L690)

#### Signature

```python
def generic_visit(self, node: AST) -> None:
    ...
```

### RecordReader().visit_AnnAssign

[Show source in type_inference.py:633](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L633)

#### Signature

```python
def visit_AnnAssign(self, node: AnnAssign) -> None:
    ...
```

### RecordReader().visit_Assign

[Show source in type_inference.py:669](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L669)

#### Signature

```python
def visit_Assign(self, node: Assign) -> None:
    ...
```

### RecordReader().visit_ClassDef

[Show source in type_inference.py:661](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L661)

#### Signature

```python
def visit_ClassDef(self, node: ClassDef) -> None:
    ...
```

### RecordReader().visit_Expr

[Show source in type_inference.py:684](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L684)

#### Signature

```python
def visit_Expr(self, node: Expr) -> None:
    ...
```

### RecordReader().visit_Pass

[Show source in type_inference.py:666](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L666)

#### Signature

```python
def visit_Pass(self, node: Pass) -> None:
    ...
```



## typed_ast

[Show source in type_inference.py:694](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/type_inference.py#L694)

#### Signature

```python
def typed_ast(ast: AST):
    ...
```