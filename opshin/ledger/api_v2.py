"""
The PlutusV2 ledger API.
All classes involved in defining the ScriptContext passed by the node.
"""
from dataclasses import dataclass
from typing import Dict, List, Union

from pycardano import Datum as Anything, PlutusData


# Plutus V2
@dataclass(unsafe_hash=True)
class TxId(PlutusData):
    """
    A transaction id, a 64 bytes long hash of the transaction body (also called transaction hash).

    Example value: TxId(bytes.fromhex("842a4d37b036da6ab3c04331240e67d81746beb44f23ad79703e026705361956"))
    """

    tx_id: bytes


@dataclass(unsafe_hash=True)
class Nothing(PlutusData):
    """
    Nothing, can be used to signify non-importance of a parameter to a function

    Example value: Nothing()
    """

    # The maximimum constructor ID for simple cbor types, chosen to minimize probability of collision while keeping the corresponding cbor small
    CONSTR_ID = 6


@dataclass(unsafe_hash=True)
class TrueData(PlutusData):
    """
    A Datum that represents True in Haskell implementations.
    It is thus used as an encoding for True in the ScriptContext.

    Example value: TrueData()
    """

    CONSTR_ID = 0


@dataclass(unsafe_hash=True)
class FalseData(PlutusData):
    """
    A Datum that represents False in Haskell implementations.
    It is thus used as an encoding for False in the ScriptContext.

    Example value: FalseData()
    """

    CONSTR_ID = 1


# A Datum that represents a boolean value in Haskell implementations.
# It is thus used as an encoding for booleans in the ScriptContext.
#
# Example value: TrueData()
BoolData = Union[TrueData, FalseData]


@dataclass(unsafe_hash=True)
class TxOutRef(PlutusData):
    """
    A reference to a transaction output (hash/id + index)
    """

    id: TxId
    idx: int


# A public key hash, used to identify signatures provided by a wallet
PubKeyHash = bytes


@dataclass(unsafe_hash=True)
class PubKeyCredential(PlutusData):
    """
    Part of an address that is authenticated by a public key hash

    Example value: PubKeyCredential(bytes.fromhex("c06ddaad12fc4ded18e56feac72957c1aa75fce6096b40e63ec88274"))
    """

    CONSTR_ID = 0
    credential_hash: PubKeyHash


# A validator hash, used to identify signatures provided by a smart contract
ValidatorHash = bytes


@dataclass(unsafe_hash=True)
class ScriptCredential(PlutusData):
    """
    Part of an address that is authenticated by a smart cotnract

    Example value: ScriptCredential(bytes.fromhex("c06ddaad12fc4ded18e56feac72957c1aa75fce6096b40e63ec88274"))
    """

    CONSTR_ID = 1
    credential_hash: ValidatorHash


# A credential, either smart contract or public key hash
Credential = Union[PubKeyCredential, ScriptCredential]


@dataclass(unsafe_hash=True)
class StakingHash(PlutusData):
    """
    Indicates that the stake of this address is controlled by the associated credential
    """

    CONSTR_ID = 0
    value: Credential


@dataclass(unsafe_hash=True)
class StakingPtr(PlutusData):
    """
    Indicates that the stake of this address is controlled by the associated pointer.

    In an address, a chain pointer refers to a point of the chain containing a stake key registration certificate.
    A point is identified by the 3 coordinates in this object.
    """

    CONSTR_ID = 1
    # an absolute slot number
    slot_no: int
    # a transaction index (within that slot)
    tx_index: int
    # a (delegation) certificate index (within that transaction)
    cert_index: int


# Part of an address that controls who can delegate the stake associated with an address
StakingCredential = Union[StakingHash, StakingPtr]


@dataclass(unsafe_hash=True)
class NoStakingCredential(PlutusData):
    """
    Indicates that this address has no staking credentials.
    Its funds can not be delegated.
    """

    CONSTR_ID = 1


@dataclass(unsafe_hash=True)
class SomeStakingCredential(PlutusData):
    """
    Indicates that this address has staking credentials.
    Its funds can be delegated by the credentialed user.
    """

    CONSTR_ID = 0
    staking_credential: StakingCredential


@dataclass(unsafe_hash=True)
class Address(PlutusData):
    """
    A Shelley address, consisting of a payment and staking credential
    """

    payment_credential: Credential
    staking_credential: Union[NoStakingCredential, SomeStakingCredential]


# The policy Id of a token
PolicyId = bytes

# The name of a token in bytes (not textual representation!)
TokenName = bytes

# The Plutus representation of amounts of tokens being spent, sent or minted
# It is a two-layered dictionary that stores for each policy id and token name
# the amount of the token that is being sent/minted/burned etc
#
# Lovelace is represented with policy id b"" and token name b""
Value = Dict[PolicyId, Dict[TokenName, int]]

# A hash of a Datum
DatumHash = bytes


@dataclass(unsafe_hash=True)
class SomeDatumHash(PlutusData):
    """
    Indicates that there is a datum associated with this output, which has the given hash.
    """

    CONSTR_ID = 1
    datum_hash: DatumHash


@dataclass(unsafe_hash=True)
class SomeScriptHash(PlutusData):
    """
    Indicates that there is a script associated with this output, which has the given hash.
    """

    CONSTR_ID = 0
    script_hash: DatumHash


# The abstract super type of any object in opshin.
# Use if you don't know what kind of object is being passed or if it doesn't matter.
BuiltinData = Anything


# An abstract type annotation that something is supposed to be used as a redeemer.
Redeemer = BuiltinData


# An abstract type annotation that something is supposed to be used as a datum.
Datum = BuiltinData


@dataclass(unsafe_hash=True)
class NoOutputDatum(PlutusData):
    """
    Indicates that there is no datum associated with an output
    """

    CONSTR_ID = 0


@dataclass(unsafe_hash=True)
class SomeOutputDatumHash(PlutusData):
    """
    Indicates that there is an datum associated with an output, which has the attached hash
    """

    CONSTR_ID = 1
    datum_hash: DatumHash


@dataclass(unsafe_hash=True)
class SomeOutputDatum(PlutusData):
    """
    Indicates that there is an datum associated with an output, which is inlined and equal to the attached datum
    """

    CONSTR_ID = 2
    datum: Datum


# Possible cases of datum association with an output
OutputDatum = Union[NoOutputDatum, SomeOutputDatumHash, SomeOutputDatum]


@dataclass(unsafe_hash=True)
class NoScriptHash(PlutusData):
    """
    Indicates that there is no script associated with an output
    """

    CONSTR_ID = 1


@dataclass(unsafe_hash=True)
class TxOut(PlutusData):
    """
    The plutus representation of an transaction output, consisting of
    - address: address owning this output
    - value: tokens associated with this output
    - datum: datum associated with this output
    - reference_script: reference script associated with this output
    """

    address: Address
    value: Value
    datum: OutputDatum
    reference_script: Union[NoScriptHash, SomeScriptHash]


@dataclass(unsafe_hash=True)
class TxInInfo(PlutusData):
    """
    The plutus representation of an transaction output, that is consumed by the transaction.
    """

    out_ref: TxOutRef
    resolved: TxOut


@dataclass(unsafe_hash=True)
class DCertDelegRegKey(PlutusData):
    CONSTR_ID = 0
    value: StakingCredential


@dataclass(unsafe_hash=True)
class DCertDelegDeRegKey(PlutusData):
    CONSTR_ID = 1
    value: StakingCredential


@dataclass(unsafe_hash=True)
class DCertDelegDelegate(PlutusData):
    CONSTR_ID = 2
    delegator: StakingCredential
    delegatee: PubKeyHash


@dataclass(unsafe_hash=True)
class DCertPoolRegister(PlutusData):
    CONSTR_ID = 3
    pool_id: PubKeyHash
    pool_vfr: PubKeyHash


@dataclass(unsafe_hash=True)
class DCertPoolRetire(PlutusData):
    CONSTR_ID = 4
    retirement_certificate: PubKeyHash
    epoch: int


@dataclass(unsafe_hash=True)
class DCertGenesis(PlutusData):
    CONSTR_ID = 5


@dataclass(unsafe_hash=True)
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


@dataclass(unsafe_hash=True)
class NegInfPOSIXTime(PlutusData):
    """
    Negative infinite POSIX time, used to indicate that there is no lower bound for the execution of this transaction
    """

    CONSTR_ID = 0


@dataclass(unsafe_hash=True)
class FinitePOSIXTime(PlutusData):
    """
    Finite POSIX time, used to indicate that there is a lower or upper bound for the execution of this transaction
    """

    CONSTR_ID = 1
    time: POSIXTime


@dataclass(unsafe_hash=True)
class PosInfPOSIXTime(PlutusData):
    """
    Infinite POSIX time, used to indicate that there is no upper bound for the execution of this transaction
    """

    CONSTR_ID = 2


ExtendedPOSIXTime = Union[NegInfPOSIXTime, FinitePOSIXTime, PosInfPOSIXTime]


@dataclass(unsafe_hash=True)
class UpperBoundPOSIXTime(PlutusData):
    """
    Upper bound for the execution of this transaction
    """

    CONSTR_ID = 0
    limit: ExtendedPOSIXTime
    closed: BoolData


@dataclass(unsafe_hash=True)
class LowerBoundPOSIXTime(PlutusData):
    """
    Lower bound for the execution of this transaction
    """

    CONSTR_ID = 0
    limit: ExtendedPOSIXTime
    closed: BoolData


@dataclass(unsafe_hash=True)
class POSIXTimeRange(PlutusData):
    """
    Time range in which this transaction can be executed
    """

    lower_bound: LowerBoundPOSIXTime
    upper_bound: UpperBoundPOSIXTime


@dataclass(unsafe_hash=True)
class Minting(PlutusData):
    """
    Script purpose indicating that the given policy id is being minted or burned
    """

    CONSTR_ID = 0
    policy_id: PolicyId


@dataclass(unsafe_hash=True)
class Spending(PlutusData):
    """
    Script purpose indicating that the given transaction output is being spent, which is
    owned by the invoked contract
    """

    CONSTR_ID = 1
    tx_out_ref: TxOutRef


@dataclass(unsafe_hash=True)
class Rewarding(PlutusData):
    CONSTR_ID = 2
    staking_credential: StakingCredential


@dataclass(unsafe_hash=True)
class Certifying(PlutusData):
    CONSTR_ID = 3
    d_cert: DCert


# The reason that this script is being invoked
ScriptPurpose = Union[Minting, Spending, Rewarding, Certifying]


@dataclass(unsafe_hash=True)
class TxInfo(PlutusData):
    """
    A complex agglomeration of everything that could be of interest to the executed script, regarding the transaction
    that invoked the script
    """

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


@dataclass(unsafe_hash=True)
class ScriptContext(PlutusData):
    """
    Auxiliary information about the transaction and reason for invocation of the called script.
    """

    tx_info: TxInfo
    purpose: ScriptPurpose
