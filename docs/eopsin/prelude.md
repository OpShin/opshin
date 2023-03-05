# Prelude

[eopsin Index](../README.md#eopsin-index) /
[Eopsin](./index.md#eopsin) /
Prelude

> Auto-generated documentation for [eopsin.prelude](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py) module.

- [Prelude](#prelude)
  - [Address](#address)
  - [Certifying](#certifying)
  - [DCertDelegDeRegKey](#dcertdelegderegkey)
  - [DCertDelegDelegate](#dcertdelegdelegate)
  - [DCertDelegRegKey](#dcertdelegregkey)
  - [DCertGenesis](#dcertgenesis)
  - [DCertMir](#dcertmir)
  - [DCertPoolRegister](#dcertpoolregister)
  - [DCertPoolRetire](#dcertpoolretire)
  - [FalseData](#falsedata)
  - [FinitePOSIXTime](#finiteposixtime)
  - [LowerBoundPOSIXTime](#lowerboundposixtime)
  - [Minting](#minting)
  - [NegInfPOSIXTime](#neginfposixtime)
  - [NoOutputDatum](#nooutputdatum)
  - [NoScriptHash](#noscripthash)
  - [NoStakingCredential](#nostakingcredential)
  - [Nothing](#nothing)
  - [POSIXTimeRange](#posixtimerange)
  - [PosInfPOSIXTime](#posinfposixtime)
  - [PubKeyCredential](#pubkeycredential)
  - [Rewarding](#rewarding)
  - [ScriptContext](#scriptcontext)
  - [ScriptCredential](#scriptcredential)
  - [SomeDatumHash](#somedatumhash)
  - [SomeOutputDatum](#someoutputdatum)
  - [SomeOutputDatumHash](#someoutputdatumhash)
  - [SomeScriptHash](#somescripthash)
  - [SomeStakingCredential](#somestakingcredential)
  - [Spending](#spending)
  - [StakingHash](#stakinghash)
  - [StakingPtr](#stakingptr)
  - [Token](#token)
  - [TrueData](#truedata)
  - [TxId](#txid)
  - [TxInInfo](#txininfo)
  - [TxInfo](#txinfo)
  - [TxOut](#txout)
  - [TxOutRef](#txoutref)
  - [UpperBoundPOSIXTime](#upperboundposixtime)
  - [all_tokens_locked_at_address](#all_tokens_locked_at_address)
  - [all_tokens_locked_at_address_with_datum](#all_tokens_locked_at_address_with_datum)
  - [all_tokens_unlocked_from_address](#all_tokens_unlocked_from_address)
  - [resolve_spent_utxo](#resolve_spent_utxo)

## Address

[Show source in prelude.py:95](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L95)

#### Signature

```python
class Address(PlutusData):
    ...
```



## Certifying

[Show source in prelude.py:284](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L284)

#### Signature

```python
class Certifying(PlutusData):
    ...
```



## DCertDelegDeRegKey

[Show source in prelude.py:176](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L176)

#### Signature

```python
class DCertDelegDeRegKey(PlutusData):
    ...
```



## DCertDelegDelegate

[Show source in prelude.py:182](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L182)

#### Signature

```python
class DCertDelegDelegate(PlutusData):
    ...
```



## DCertDelegRegKey

[Show source in prelude.py:170](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L170)

#### Signature

```python
class DCertDelegRegKey(PlutusData):
    ...
```



## DCertGenesis

[Show source in prelude.py:203](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L203)

#### Signature

```python
class DCertGenesis(PlutusData):
    ...
```



## DCertMir

[Show source in prelude.py:208](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L208)

#### Signature

```python
class DCertMir(PlutusData):
    ...
```



## DCertPoolRegister

[Show source in prelude.py:189](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L189)

#### Signature

```python
class DCertPoolRegister(PlutusData):
    ...
```



## DCertPoolRetire

[Show source in prelude.py:196](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L196)

#### Signature

```python
class DCertPoolRetire(PlutusData):
    ...
```



## FalseData

[Show source in prelude.py:25](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L25)

#### Signature

```python
class FalseData(PlutusData):
    ...
```



## FinitePOSIXTime

[Show source in prelude.py:232](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L232)

#### Signature

```python
class FinitePOSIXTime(PlutusData):
    ...
```



## LowerBoundPOSIXTime

[Show source in prelude.py:253](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L253)

#### Signature

```python
class LowerBoundPOSIXTime(PlutusData):
    ...
```



## Minting

[Show source in prelude.py:266](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L266)

#### Signature

```python
class Minting(PlutusData):
    ...
```



## NegInfPOSIXTime

[Show source in prelude.py:227](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L227)

#### Signature

```python
class NegInfPOSIXTime(PlutusData):
    ...
```



## NoOutputDatum

[Show source in prelude.py:131](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L131)

#### Signature

```python
class NoOutputDatum(PlutusData):
    ...
```



## NoScriptHash

[Show source in prelude.py:151](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L151)

#### Signature

```python
class NoScriptHash(PlutusData):
    ...
```



## NoStakingCredential

[Show source in prelude.py:84](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L84)

#### Signature

```python
class NoStakingCredential(PlutusData):
    ...
```



## Nothing

[Show source in prelude.py:14](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L14)

#### Attributes

- `CONSTR_ID` - The maximimum constructor ID for simple cbor types, chosen to minimize probability of collision while keeping the corresponding cbor small: `6`


#### Signature

```python
class Nothing(PlutusData):
    ...
```



## POSIXTimeRange

[Show source in prelude.py:260](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L260)

#### Signature

```python
class POSIXTimeRange(PlutusData):
    ...
```



## PosInfPOSIXTime

[Show source in prelude.py:238](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L238)

#### Signature

```python
class PosInfPOSIXTime(PlutusData):
    ...
```



## PubKeyCredential

[Show source in prelude.py:42](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L42)

#### Signature

```python
class PubKeyCredential(PlutusData):
    ...
```



## Rewarding

[Show source in prelude.py:278](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L278)

#### Signature

```python
class Rewarding(PlutusData):
    ...
```



## ScriptContext

[Show source in prelude.py:309](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L309)

#### Signature

```python
class ScriptContext(PlutusData):
    ...
```



## ScriptCredential

[Show source in prelude.py:51](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L51)

#### Signature

```python
class ScriptCredential(PlutusData):
    ...
```



## SomeDatumHash

[Show source in prelude.py:110](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L110)

#### Signature

```python
class SomeDatumHash(PlutusData):
    ...
```



## SomeOutputDatum

[Show source in prelude.py:142](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L142)

#### Signature

```python
class SomeOutputDatum(PlutusData):
    ...
```



## SomeOutputDatumHash

[Show source in prelude.py:136](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L136)

#### Signature

```python
class SomeOutputDatumHash(PlutusData):
    ...
```



## SomeScriptHash

[Show source in prelude.py:116](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L116)

#### Signature

```python
class SomeScriptHash(PlutusData):
    ...
```



## SomeStakingCredential

[Show source in prelude.py:89](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L89)

#### Signature

```python
class SomeStakingCredential(PlutusData):
    ...
```



## Spending

[Show source in prelude.py:272](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L272)

#### Signature

```python
class Spending(PlutusData):
    ...
```



## StakingHash

[Show source in prelude.py:60](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L60)

#### Signature

```python
class StakingHash(PlutusData):
    ...
```



## StakingPtr

[Show source in prelude.py:66](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L66)

In an address, a chain pointer refers to a point of the chain containing a stake key registration certificate. A point is identified by 3 coordinates.

#### Signature

```python
class StakingPtr(PlutusData):
    ...
```



## Token

[Show source in prelude.py:315](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L315)

#### Signature

```python
class Token(PlutusData):
    ...
```



## TrueData

[Show source in prelude.py:20](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L20)

#### Signature

```python
class TrueData(PlutusData):
    ...
```



## TxId

[Show source in prelude.py:9](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L9)

#### Signature

```python
class TxId(PlutusData):
    ...
```



## TxInInfo

[Show source in prelude.py:164](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L164)

#### Signature

```python
class TxInInfo(PlutusData):
    ...
```



## TxInfo

[Show source in prelude.py:293](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L293)

#### Signature

```python
class TxInfo(PlutusData):
    ...
```



## TxOut

[Show source in prelude.py:156](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L156)

#### Signature

```python
class TxOut(PlutusData):
    ...
```



## TxOutRef

[Show source in prelude.py:33](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L33)

#### Signature

```python
class TxOutRef(PlutusData):
    ...
```



## UpperBoundPOSIXTime

[Show source in prelude.py:246](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L246)

#### Signature

```python
class UpperBoundPOSIXTime(PlutusData):
    ...
```



## all_tokens_locked_at_address

[Show source in prelude.py:351](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L351)

Returns how many tokens of specified type are locked at then given address

#### Signature

```python
def all_tokens_locked_at_address(
    txouts: List[TxOut], address: Address, token: Token
) -> int:
    ...
```

#### See also

- [Address](#address)
- [Token](#token)



## all_tokens_locked_at_address_with_datum

[Show source in prelude.py:338](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L338)

Returns how many tokens of specified type are locked at then given address with the specified datum

#### Signature

```python
def all_tokens_locked_at_address_with_datum(
    txouts: List[TxOut], address: Address, token: Token, output_datum: OutputDatum
) -> int:
    ...
```

#### See also

- [Address](#address)
- [OutputDatum](#outputdatum)
- [Token](#token)



## all_tokens_unlocked_from_address

[Show source in prelude.py:325](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L325)

Returns how many tokens of specified type are unlocked from given address

#### Signature

```python
def all_tokens_unlocked_from_address(
    txins: List[TxInInfo], address: Address, token: Token
) -> int:
    ...
```

#### See also

- [Address](#address)
- [Token](#token)



## resolve_spent_utxo

[Show source in prelude.py:364](https://github.com/ImperatorLang/eopsin/blob/feat/docs/eopsin/prelude.py#L364)

Returns the UTxO whose spending should be validated

#### Signature

```python
def resolve_spent_utxo(txins: List[TxInInfo], p: Spending) -> TxOut:
    ...
```

#### See also

- [Spending](#spending)
- [TxOut](#txout)