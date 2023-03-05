# TypedAST

[Eopsin-lang Index](../README.md#eopsin-lang-index) /
[Eopsin](./index.md#eopsin) /
TypedAST

> Auto-generated documentation for [eopsin.typed_ast](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py) module.

- [TypedAST](#typedast)
  - [AnyType](#anytype)
  - [AtomicType](#atomictype)
  - [BoolType](#booltype)
    - [BoolType().cmp](#booltype()cmp)
  - [ByteStringType](#bytestringtype)
    - [ByteStringType().attribute](#bytestringtype()attribute)
    - [ByteStringType().attribute_type](#bytestringtype()attribute_type)
    - [ByteStringType().cmp](#bytestringtype()cmp)
    - [ByteStringType().constr](#bytestringtype()constr)
    - [ByteStringType().constr_type](#bytestringtype()constr_type)
  - [ClassType](#classtype)
  - [DictType](#dicttype)
    - [DictType().attribute](#dicttype()attribute)
    - [DictType().attribute_type](#dicttype()attribute_type)
  - [FunctionType](#functiontype)
  - [InaccessibleType](#inaccessibletype)
  - [InstanceType](#instancetype)
    - [InstanceType().attribute](#instancetype()attribute)
    - [InstanceType().attribute_type](#instancetype()attribute_type)
    - [InstanceType().cmp](#instancetype()cmp)
    - [InstanceType().constr](#instancetype()constr)
    - [InstanceType().constr_type](#instancetype()constr_type)
  - [IntegerType](#integertype)
    - [IntegerType().cmp](#integertype()cmp)
    - [IntegerType().constr](#integertype()constr)
    - [IntegerType().constr_type](#integertype()constr_type)
  - [ListType](#listtype)
  - [PolymorphicFunction](#polymorphicfunction)
    - [PolymorphicFunction().impl_from_args](#polymorphicfunction()impl_from_args)
    - [PolymorphicFunction().type_from_args](#polymorphicfunction()type_from_args)
  - [PolymorphicFunctionInstanceType](#polymorphicfunctioninstancetype)
  - [PolymorphicFunctionType](#polymorphicfunctiontype)
  - [RawPlutoExpr](#rawplutoexpr)
  - [Record](#record)
  - [RecordType](#recordtype)
    - [RecordType().attribute](#recordtype()attribute)
    - [RecordType().attribute_type](#recordtype()attribute_type)
    - [RecordType().cmp](#recordtype()cmp)
    - [RecordType().constr](#recordtype()constr)
    - [RecordType().constr_type](#recordtype()constr_type)
  - [StringType](#stringtype)
    - [StringType().attribute](#stringtype()attribute)
    - [StringType().attribute_type](#stringtype()attribute_type)
    - [StringType().cmp](#stringtype()cmp)
    - [StringType().constr](#stringtype()constr)
    - [StringType().constr_type](#stringtype()constr_type)
  - [TupleType](#tupletype)
  - [Type](#type)
    - [Type().attribute](#type()attribute)
    - [Type().attribute_type](#type()attribute_type)
    - [Type().cmp](#type()cmp)
    - [Type().constr](#type()constr)
    - [Type().constr_type](#type()constr_type)
  - [TypeInferenceError](#typeinferenceerror)
  - [TypedAST](#typedast-1)
  - [TypedAnnAssign](#typedannassign)
  - [TypedAssert](#typedassert)
  - [TypedAssign](#typedassign)
  - [TypedAttribute](#typedattribute)
  - [TypedBinOp](#typedbinop)
  - [TypedBoolOp](#typedboolop)
  - [TypedCall](#typedcall)
  - [TypedClassDef](#typedclassdef)
  - [TypedCompare](#typedcompare)
  - [TypedConstant](#typedconstant)
  - [TypedDict](#typeddict)
  - [TypedExpr](#typedexpr)
  - [TypedExpression](#typedexpression)
  - [TypedFor](#typedfor)
  - [TypedFunctionDef](#typedfunctiondef)
  - [TypedIf](#typedif)
  - [TypedIfExp](#typedifexp)
  - [TypedList](#typedlist)
  - [TypedListComp](#typedlistcomp)
  - [TypedModule](#typedmodule)
  - [TypedName](#typedname)
  - [TypedNodeTransformer](#typednodetransformer)
    - [TypedNodeTransformer().visit](#typednodetransformer()visit)
  - [TypedNodeVisitor](#typednodevisitor)
    - [TypedNodeVisitor().visit](#typednodevisitor()visit)
  - [TypedPass](#typedpass)
  - [TypedReturn](#typedreturn)
  - [TypedSubscript](#typedsubscript)
  - [TypedTuple](#typedtuple)
  - [TypedUnaryOp](#typedunaryop)
  - [TypedWhile](#typedwhile)
  - [UnionType](#uniontype)
    - [UnionType().attribute](#uniontype()attribute)
    - [UnionType().attribute_type](#uniontype()attribute_type)
    - [UnionType().cmp](#uniontype()cmp)
  - [UnitType](#unittype)
    - [UnitType().cmp](#unittype()cmp)
  - [typedarg](#typedarg)
  - [typedarguments](#typedarguments)
  - [typedcomprehension](#typedcomprehension)
  - [typedexpr](#typedexpr)
  - [typedstmt](#typedstmt)
  - [FrozenFrozenList](#frozenfrozenlist)
  - [distinct](#distinct)
  - [empty_list](#empty_list)
  - [transform_ext_params_map](#transform_ext_params_map)
  - [transform_output_map](#transform_output_map)

## AnyType

[Show source in typed_ast.py:64](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L64)

The top element in the partial order on types

#### Signature

```python
class AnyType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)



## AtomicType

[Show source in typed_ast.py:72](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L72)

#### Signature

```python
class AtomicType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)



## BoolType

[Show source in typed_ast.py:762](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L762)

#### Signature

```python
class BoolType(AtomicType):
    ...
```

#### See also

- [AtomicType](#atomictype)

### BoolType().cmp

[Show source in typed_ast.py:763](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L763)

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```



## ByteStringType

[Show source in typed_ast.py:671](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L671)

#### Signature

```python
class ByteStringType(AtomicType):
    ...
```

#### See also

- [AtomicType](#atomictype)

### ByteStringType().attribute

[Show source in typed_ast.py:694](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L694)

#### Signature

```python
def attribute(self, attr) -> plt.AST:
    ...
```

### ByteStringType().attribute_type

[Show source in typed_ast.py:689](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L689)

#### Signature

```python
def attribute_type(self, attr) -> Type:
    ...
```

#### See also

- [Type](#type)

### ByteStringType().cmp

[Show source in typed_ast.py:700](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L700)

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```

### ByteStringType().constr

[Show source in typed_ast.py:679](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L679)

#### Signature

```python
def constr(self) -> plt.AST:
    ...
```

### ByteStringType().constr_type

[Show source in typed_ast.py:672](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L672)

#### Signature

```python
def constr_type(self) -> InstanceType:
    ...
```

#### See also

- [InstanceType](#instancetype)



## ClassType

[Show source in typed_ast.py:58](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L58)

#### Signature

```python
class ClassType(Type):
    ...
```

#### See also

- [Type](#type)



## DictType

[Show source in typed_ast.py:292](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L292)

#### Signature

```python
class DictType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)

### DictType().attribute

[Show source in typed_ast.py:311](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L311)

#### Signature

```python
def attribute(self, attr) -> plt.AST:
    ...
```

### DictType().attribute_type

[Show source in typed_ast.py:296](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L296)

#### Signature

```python
def attribute_type(self, attr) -> "Type":
    ...
```



## FunctionType

[Show source in typed_ast.py:376](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L376)

#### Signature

```python
class FunctionType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)



## InaccessibleType

[Show source in typed_ast.py:812](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L812)

A type that blocks overwriting of a function

#### Signature

```python
class InaccessibleType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)



## InstanceType

[Show source in typed_ast.py:389](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L389)

#### Signature

```python
class InstanceType(Type):
    ...
```

#### See also

- [Type](#type)

### InstanceType().attribute

[Show source in typed_ast.py:401](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L401)

#### Signature

```python
def attribute(self, attr) -> plt.AST:
    ...
```

### InstanceType().attribute_type

[Show source in typed_ast.py:398](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L398)

#### Signature

```python
def attribute_type(self, attr) -> Type:
    ...
```

#### See also

- [Type](#type)

### InstanceType().cmp

[Show source in typed_ast.py:404](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L404)

The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison.

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```

### InstanceType().constr

[Show source in typed_ast.py:395](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L395)

#### Signature

```python
def constr(self) -> plt.AST:
    ...
```

### InstanceType().constr_type

[Show source in typed_ast.py:392](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L392)

#### Signature

```python
def constr_type(self) -> FunctionType:
    ...
```

#### See also

- [FunctionType](#functiontype)



## IntegerType

[Show source in typed_ast.py:415](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L415)

#### Signature

```python
class IntegerType(AtomicType):
    ...
```

#### See also

- [AtomicType](#atomictype)

### IntegerType().cmp

[Show source in typed_ast.py:506](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L506)

The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison.

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```

### IntegerType().constr

[Show source in typed_ast.py:419](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L419)

#### Signature

```python
def constr(self) -> plt.AST:
    ...
```

### IntegerType().constr_type

[Show source in typed_ast.py:416](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L416)

#### Signature

```python
def constr_type(self) -> InstanceType:
    ...
```

#### See also

- [InstanceType](#instancetype)



## ListType

[Show source in typed_ast.py:284](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L284)

#### Signature

```python
class ListType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)



## PolymorphicFunction

[Show source in typed_ast.py:818](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L818)

#### Signature

```python
class PolymorphicFunction:
    ...
```

### PolymorphicFunction().impl_from_args

[Show source in typed_ast.py:822](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L822)

#### Signature

```python
def impl_from_args(self, args: typing.List[Type]) -> plt.AST:
    ...
```

### PolymorphicFunction().type_from_args

[Show source in typed_ast.py:819](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L819)

#### Signature

```python
def type_from_args(self, args: typing.List[Type]) -> FunctionType:
    ...
```

#### See also

- [FunctionType](#functiontype)



## PolymorphicFunctionInstanceType

[Show source in typed_ast.py:834](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L834)

#### Signature

```python
class PolymorphicFunctionInstanceType(InstanceType):
    ...
```

#### See also

- [InstanceType](#instancetype)



## PolymorphicFunctionType

[Show source in typed_ast.py:827](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L827)

A special type of builtin that may act differently on different parameters

#### Signature

```python
class PolymorphicFunctionType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)



## RawPlutoExpr

[Show source in typed_ast.py:999](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L999)

#### Signature

```python
class RawPlutoExpr(typedexpr):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## Record

[Show source in typed_ast.py:51](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L51)

#### Signature

```python
class Record:
    ...
```



## RecordType

[Show source in typed_ast.py:79](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L79)

#### Signature

```python
class RecordType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)

### RecordType().attribute

[Show source in typed_ast.py:111](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L111)

The attributes of this class. Need to be a lambda that expects as first argument the object itself

#### Signature

```python
def attribute(self, attr: str) -> plt.AST:
    ...
```

### RecordType().attribute_type

[Show source in typed_ast.py:100](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L100)

The types of the named attributes of this class

#### Signature

```python
def attribute_type(self, attr: str) -> Type:
    ...
```

#### See also

- [Type](#type)

### RecordType().cmp

[Show source in typed_ast.py:132](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L132)

The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison.

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```

### RecordType().constr

[Show source in typed_ast.py:87](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L87)

#### Signature

```python
def constr(self) -> plt.AST:
    ...
```

### RecordType().constr_type

[Show source in typed_ast.py:82](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L82)

#### Signature

```python
def constr_type(self) -> "InstanceType":
    ...
```



## StringType

[Show source in typed_ast.py:581](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L581)

#### Signature

```python
class StringType(AtomicType):
    ...
```

#### See also

- [AtomicType](#atomictype)

### StringType().attribute

[Show source in typed_ast.py:657](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L657)

#### Signature

```python
def attribute(self, attr) -> plt.AST:
    ...
```

### StringType().attribute_type

[Show source in typed_ast.py:652](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L652)

#### Signature

```python
def attribute_type(self, attr) -> Type:
    ...
```

#### See also

- [Type](#type)

### StringType().cmp

[Show source in typed_ast.py:663](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L663)

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```

### StringType().constr

[Show source in typed_ast.py:585](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L585)

#### Signature

```python
def constr(self) -> plt.AST:
    ...
```

### StringType().constr_type

[Show source in typed_ast.py:582](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L582)

#### Signature

```python
def constr_type(self) -> InstanceType:
    ...
```

#### See also

- [InstanceType](#instancetype)



## TupleType

[Show source in typed_ast.py:274](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L274)

#### Signature

```python
class TupleType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)



## Type

[Show source in typed_ast.py:22](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L22)

#### Signature

```python
class Type:
    ...
```

### Type().attribute

[Show source in typed_ast.py:39](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L39)

The attributes of this class. Needs to be a lambda that expects as first argument the object itself

#### Signature

```python
def attribute(self, attr) -> plt.AST:
    ...
```

### Type().attribute_type

[Show source in typed_ast.py:33](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L33)

The types of the named attributes of this class

#### Signature

```python
def attribute_type(self, attr) -> "Type":
    ...
```

### Type().cmp

[Show source in typed_ast.py:43](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L43)

The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison.

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```

### Type().constr

[Show source in typed_ast.py:29](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L29)

The constructor for this class

#### Signature

```python
def constr(self) -> plt.AST:
    ...
```

### Type().constr_type

[Show source in typed_ast.py:23](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L23)

The type of the constructor for this class

#### Signature

```python
def constr_type(self) -> "InstanceType":
    ...
```



## TypeInferenceError

[Show source in typed_ast.py:1004](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L1004)

#### Signature

```python
class TypeInferenceError(AssertionError):
    ...
```



## TypedAST

[Show source in typed_ast.py:839](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L839)

#### Signature

```python
class TypedAST(AST):
    ...
```



## TypedAnnAssign

[Show source in typed_ast.py:906](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L906)

#### Signature

```python
class TypedAnnAssign(typedstmt, AnnAssign):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedAssert

[Show source in typed_ast.py:994](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L994)

#### Signature

```python
class TypedAssert(typedstmt, Assert):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedAssign

[Show source in typed_ast.py:897](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L897)

#### Signature

```python
class TypedAssign(typedstmt, Assign):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedAttribute

[Show source in typed_ast.py:989](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L989)

#### Signature

```python
class TypedAttribute(typedexpr, Attribute):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedBinOp

[Show source in typed_ast.py:972](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L972)

#### Signature

```python
class TypedBinOp(typedexpr, BinOp):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedBoolOp

[Show source in typed_ast.py:977](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L977)

#### Signature

```python
class TypedBoolOp(typedexpr, BoolOp):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedCall

[Show source in typed_ast.py:888](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L888)

#### Signature

```python
class TypedCall(typedexpr, Call):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedClassDef

[Show source in typed_ast.py:902](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L902)

#### Signature

```python
class TypedClassDef(typedstmt, ClassDef):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedCompare

[Show source in typed_ast.py:966](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L966)

#### Signature

```python
class TypedCompare(typedexpr, Compare):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedConstant

[Show source in typed_ast.py:933](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L933)

#### Signature

```python
class TypedConstant(TypedAST, Constant):
    ...
```

#### See also

- [TypedAST](#typedast)



## TypedDict

[Show source in typed_ast.py:956](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L956)

#### Signature

```python
class TypedDict(typedexpr, Dict):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedExpr

[Show source in typed_ast.py:893](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L893)

#### Signature

```python
class TypedExpr(typedstmt, Expr):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedExpression

[Show source in typed_ast.py:884](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L884)

#### Signature

```python
class TypedExpression(typedexpr, Expression):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedFor

[Show source in typed_ast.py:918](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L918)

#### Signature

```python
class TypedFor(typedstmt, For):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedFunctionDef

[Show source in typed_ast.py:869](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L869)

#### Signature

```python
class TypedFunctionDef(typedstmt, FunctionDef):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedIf

[Show source in typed_ast.py:874](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L874)

#### Signature

```python
class TypedIf(typedstmt, If):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedIfExp

[Show source in typed_ast.py:960](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L960)

#### Signature

```python
class TypedIfExp(typedstmt, IfExp):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedList

[Show source in typed_ast.py:941](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L941)

#### Signature

```python
class TypedList(typedexpr, List):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedListComp

[Show source in typed_ast.py:951](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L951)

#### Signature

```python
class TypedListComp(typedexpr, ListComp):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedModule

[Show source in typed_ast.py:865](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L865)

#### Signature

```python
class TypedModule(typedstmt, Module):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedName

[Show source in typed_ast.py:929](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L929)

#### Signature

```python
class TypedName(typedexpr, Name):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedNodeTransformer

[Show source in typed_ast.py:1092](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L1092)

#### Signature

```python
class TypedNodeTransformer(NodeTransformer):
    ...
```

### TypedNodeTransformer().visit

[Show source in typed_ast.py:1093](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L1093)

Visit a node.

#### Signature

```python
def visit(self, node):
    ...
```



## TypedNodeVisitor

[Show source in typed_ast.py:1103](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L1103)

#### Signature

```python
class TypedNodeVisitor(NodeVisitor):
    ...
```

### TypedNodeVisitor().visit

[Show source in typed_ast.py:1104](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L1104)

Visit a node.

#### Signature

```python
def visit(self, node):
    ...
```



## TypedPass

[Show source in typed_ast.py:925](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L925)

#### Signature

```python
class TypedPass(typedstmt, Pass):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedReturn

[Show source in typed_ast.py:880](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L880)

#### Signature

```python
class TypedReturn(typedstmt, Return):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## TypedSubscript

[Show source in typed_ast.py:985](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L985)

#### Signature

```python
class TypedSubscript(typedexpr, Subscript):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedTuple

[Show source in typed_ast.py:937](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L937)

#### Signature

```python
class TypedTuple(typedexpr, Tuple):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedUnaryOp

[Show source in typed_ast.py:981](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L981)

#### Signature

```python
class TypedUnaryOp(typedexpr, UnaryOp):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## TypedWhile

[Show source in typed_ast.py:912](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L912)

#### Signature

```python
class TypedWhile(typedstmt, While):
    ...
```

#### See also

- [typedstmt](#typedstmt)



## UnionType

[Show source in typed_ast.py:185](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L185)

#### Signature

```python
class UnionType(ClassType):
    ...
```

#### See also

- [ClassType](#classtype)

### UnionType().attribute

[Show source in typed_ast.py:216](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L216)

#### Signature

```python
def attribute(self, attr: str) -> plt.AST:
    ...
```

### UnionType().attribute_type

[Show source in typed_ast.py:188](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L188)

#### Signature

```python
def attribute_type(self, attr) -> "Type":
    ...
```

### UnionType().cmp

[Show source in typed_ast.py:248](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L248)

The implementation of comparing this type to type o via operator op. Returns a lambda that expects as first argument the object itself and as second the comparison.

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```



## UnitType

[Show source in typed_ast.py:784](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L784)

#### Signature

```python
class UnitType(AtomicType):
    ...
```

#### See also

- [AtomicType](#atomictype)

### UnitType().cmp

[Show source in typed_ast.py:785](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L785)

#### Signature

```python
def cmp(self, op: cmpop, o: "Type") -> plt.AST:
    ...
```



## typedarg

[Show source in typed_ast.py:852](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L852)

#### Signature

```python
class typedarg(TypedAST, arg):
    ...
```

#### See also

- [TypedAST](#typedast)



## typedarguments

[Show source in typed_ast.py:856](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L856)

#### Signature

```python
class typedarguments(TypedAST, arguments):
    ...
```

#### See also

- [TypedAST](#typedast)



## typedcomprehension

[Show source in typed_ast.py:945](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L945)

#### Signature

```python
class typedcomprehension(typedexpr, comprehension):
    ...
```

#### See also

- [typedexpr](#typedexpr)



## typedexpr

[Show source in typed_ast.py:843](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L843)

#### Signature

```python
class typedexpr(TypedAST, expr):
    ...
```

#### See also

- [TypedAST](#typedast)



## typedstmt

[Show source in typed_ast.py:847](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L847)

#### Attributes

- `typ` - Statements always have type None: `NoneInstanceType`


#### Signature

```python
class typedstmt(TypedAST, stmt):
    ...
```

#### See also

- [TypedAST](#typedast)



## FrozenFrozenList

[Show source in typed_ast.py:16](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L16)

#### Signature

```python
def FrozenFrozenList(l: list):
    ...
```



## distinct

[Show source in typed_ast.py:11](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L11)

Returns true iff the list consists of distinct elements

#### Signature

```python
def distinct(xs: list):
    ...
```



## empty_list

[Show source in typed_ast.py:1017](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L1017)

#### Signature

```python
def empty_list(p: Type):
    ...
```

#### See also

- [Type](#type)



## transform_ext_params_map

[Show source in typed_ast.py:1040](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L1040)

#### Signature

```python
def transform_ext_params_map(p: Type):
    ...
```

#### See also

- [Type](#type)



## transform_output_map

[Show source in typed_ast.py:1071](https://github.com/ImperatorLang/eopsin/blob/main/eopsin/typed_ast.py#L1071)

#### Signature

```python
def transform_output_map(p: Type):
    ...
```

#### See also

- [Type](#type)