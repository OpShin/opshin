from pycardano import Datum, PlutusData
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

# Plutus V2
TxId = bytes


@dataclass()
class TxOutRef(PlutusData):
    id: TxId
    idx: int


PubKeyHash = bytes


@dataclass()
class PubKeyCredential(PlutusData):
    CONSTR_ID = 0
    pubkeyhash: PubKeyHash


ValidatorHash = bytes


@dataclass()
class ScriptCredential(PlutusData):
    CONSTR_ID = 1
    validator_hash: ValidatorHash


Credential = Union[PubKeyCredential, ScriptCredential]


@dataclass()
class StakingHash(PlutusData):
    CONSTR_ID = 0
    value: Credential


@dataclass()
class StakingPtr(PlutusData):
    """
    In an address, a chain pointer refers to a point of the chain containing a stake key registration certificate. A point is identified by 3 coordinates.
    """

    CONSTR_ID = 1
    # an absolute slot number
    slot_no: int
    # a transaction index (within that slot)
    tx_index: int
    # a (delegation) certificate index (within that transaction)
    cert_index: int


StakingCredential = Union[StakingHash, StakingPtr]


@dataclass()
class Address(PlutusData):
    credential: Credential
    staking_credential: Optional[StakingCredential]


CurrencySymbol = bytes

TokenName = bytes

Value = Dict[CurrencySymbol, Dict[TokenName, int]]

DatumHash = bytes


@dataclass()
class TxOut(PlutusData):
    address: Address
    value: Value
    datum_hash: Optional[DatumHash]


@dataclass()
class TxInInfo(PlutusData):
    out_ref: TxOutRef
    resolved: TxOut


@dataclass()
class DCertDelegRegKey(PlutusData):
    CONSTR_ID = 0
    value: StakingCredential


@dataclass()
class DCertDelegDeRegKey(PlutusData):
    CONSTR_ID = 1
    value: StakingCredential


@dataclass()
class DCertDelegDelegate(PlutusData):
    CONSTR_ID = 2
    delegator: StakingCredential
    delegatee: PubKeyHash


@dataclass()
class DCertPoolRegister(PlutusData):
    CONSTR_ID = 3
    pool_id: PubKeyHash
    pool_vfr: PubKeyHash


@dataclass()
class DCertPoolRetire(PlutusData):
    CONSTR_ID = 4
    retirement_certificate: PubKeyHash
    epoch: int


@dataclass()
class DCertGenesis(PlutusData):
    CONSTR_ID = 5


@dataclass()
class DCertMir(PlutusData):
    CONSTR_ID = 6


DCert = Union[
    DCertDelegRegKey,
    DCertDelegDeRegKey,
    DCertDelegDelegate,
    DCertPoolRegister,
    DCertPoolRetire,
    DCertGenesis,
    DCertMir,
]


POSIXTime = int


@dataclass()
class POSIXTimeRange(PlutusData):
    lower_bound: POSIXTime
    upper_bound: POSIXTime


@dataclass()
class Minting(PlutusData):
    currency_symbol: CurrencySymbol


@dataclass()
class Spending(PlutusData):
    tx_out_ref: TxOutRef


@dataclass()
class Rewarding(PlutusData):
    staking_credential: StakingCredential


@dataclass()
class Certifying(PlutusData):
    d_cert: DCert


ScriptPurpose = Union[Minting, Spending, Rewarding, Certifying]


@dataclass()
class BuiltinData(PlutusData):
    # TODO how to represent this -> should be possible to compare to other PlutusData
    # value: Datum
    pass


Redeemer = BuiltinData


Datum = BuiltinData


@dataclass()
class TxInfo(PlutusData):
    inputs: List[TxInInfo]
    outputs: List[TxOut]
    fee: Value
    mint: Value
    dcert: List[DCert]
    wdrl: Dict[StakingCredential, int]
    valid_range: POSIXTimeRange
    signatories: List[PubKeyHash]
    redeemers: Dict[ScriptPurpose, Redeemer]
    data: Dict[DatumHash, Datum]
    id: TxId


@dataclass()
class ScriptContext(PlutusData):
    tx_info: TxInfo
    purpose: ScriptPurpose
