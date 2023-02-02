from dataclasses import dataclass
from typing import Dict, List, Union
from hashlib import sha256, sha3_256, blake2b

from pycardano import Datum as Anything, PlutusData

# Plutus V2
TxId = bytes


@dataclass()
class Nothing(PlutusData):
    # The maximimum constructor ID for simple cbor types, chosen to minimize probability of collision while keeping the corresponding cbor small
    CONSTR_ID = 6


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
class NoStakingCredential(PlutusData):
    CONSTR_ID = 1


@dataclass()
class SomeStakingCredential(PlutusData):
    CONSTR_ID = 0
    staking_credential: StakingCredential


@dataclass()
class Address(PlutusData):
    credential: Credential
    staking_credential: Union[NoStakingCredential, SomeStakingCredential]


PolicyId = bytes

TokenName = bytes

Value = Dict[PolicyId, Dict[TokenName, int]]

DatumHash = bytes


@dataclass()
class SomeDatumHash(PlutusData):
    CONSTR_ID = 1
    datum_hash: DatumHash


@dataclass()
class SomeScriptHash(PlutusData):
    CONSTR_ID = 0
    script_hash: DatumHash


BuiltinData = Anything


Redeemer = BuiltinData


Datum = BuiltinData


@dataclass()
class NoOutputDatum(PlutusData):
    CONSTR_ID = 0


@dataclass()
class SomeOutputDatumHash(PlutusData):
    CONSTR_ID = 1
    datum_hash: DatumHash


@dataclass()
class SomeOutputDatum(PlutusData):
    CONSTR_ID = 2
    datum: Datum


OutputDatum = Union[NoOutputDatum, SomeOutputDatumHash, SomeOutputDatum]


@dataclass()
class NoScriptHash(PlutusData):
    CONSTR_ID = 1


@dataclass()
class TxOut(PlutusData):
    address: Address
    value: Value
    datum: OutputDatum
    reference_script: Union[NoScriptHash, SomeScriptHash]


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
    CONSTR_ID = 0
    policy_id: PolicyId


@dataclass()
class Spending(PlutusData):
    CONSTR_ID = 1
    tx_out_ref: TxOutRef


@dataclass()
class Rewarding(PlutusData):
    CONSTR_ID = 2
    staking_credential: StakingCredential


@dataclass()
class Certifying(PlutusData):
    CONSTR_ID = 3
    d_cert: DCert


ScriptPurpose = Union[Minting, Spending, Rewarding, Certifying]


@dataclass()
class TxInfo(PlutusData):
    inputs: List[TxInInfo]
    reference_inputs: List[TxInInfo]
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


@dataclass()
class Token(PlutusData):
    policy_id: PolicyId
    token_name: TokenName


NoRedeemer = Nothing
