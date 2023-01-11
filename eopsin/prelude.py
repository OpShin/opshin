from pycardano import Datum, PlutusData
from typing import List, Dict, Optional, Union

# Plutus V2
TxId = bytes


class TxOutRef(PlutusData):
    id: TxId
    idx: int


PubKeyHash = bytes


class PubKeyCredential(PlutusData):
    CONSTR_ID = 0
    pubkeyhash: PubKeyHash


ValidatorHash = bytes


class ScriptCredential(PlutusData):
    CONSTR_ID = 1
    validator_hash: ValidatorHash


Credential = Union[PubKeyCredential, ScriptCredential]


class StakingHash(PlutusData):
    CONSTR_ID = 0
    value: Credential


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


class Address(PlutusData):
    credential: Credential
    staking_credential: Optional[StakingCredential]


CurrencySymbol = bytes

TokenName = bytes

Value = Dict[CurrencySymbol, Dict[TokenName, int]]

DatumHash = bytes


class TxOut(PlutusData):
    address: Address
    value: Value
    datum_hash: Optional[DatumHash]


class TxInInfo(PlutusData):
    out_ref: TxOutRef
    resolved: TxOut


class DCertDelegRegKey(PlutusData):
    CONSTR_ID = 0
    value: StakingCredential


class DCertDelegDeRegKey(PlutusData):
    CONSTR_ID = 1
    value: StakingCredential


class DCertDelegDelegate(PlutusData):
    CONSTR_ID = 2
    delegator: StakingCredential
    delegatee: PubKeyHash


class DCertPoolRegister(PlutusData):
    CONSTR_ID = 3
    pool_id: PubKeyHash
    pool_vfr: PubKeyHash


class DCertPoolRetire(PlutusData):
    CONSTR_ID = 4
    retirement_certificate: PubKeyHash
    epoch: int


class DCertGenesis(PlutusData):
    CONSTR_ID = 5


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


class POSIXTimeRange(PlutusData):
    lower_bound: POSIXTime
    upper_bound: POSIXTime


class Minting(PlutusData):
    currency_symbol: CurrencySymbol


class Spending(PlutusData):
    tx_out_ref: TxOutRef


class Rewarding(PlutusData):
    staking_credential: StakingCredential


class Certifying(PlutusData):
    d_cert: DCert


ScriptPurpose = Union[Minting, Spending, Rewarding, Certifying]


class BuiltinData(PlutusData):
    # TODO how to represent this -> should be possible to compare to other PlutusData
    # value: Datum
    pass


Redeemer = BuiltinData


Datum = BuiltinData


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


class ScriptContext(PlutusData):
    tx_info: TxInfo
    purpose: ScriptPurpose
