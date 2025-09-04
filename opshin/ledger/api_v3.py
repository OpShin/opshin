"""
The PlutusV3 ledger API.
All classes involved in defining the ScriptContext passed by the node.
"""

from dataclasses import dataclass
from typing import Dict, List, Union

from pycardano import Datum as Anything, PlutusData
from opshin.std.fractions import *


@dataclass(unsafe_hash=True)
class NoScriptHash(PlutusData):
    """
    Indicates that there is no script associated with an output
    """

    CONSTR_ID = 1


# A transaction id, a 64 bytes long hash of the transaction body (also called transaction hash).
#
# Example value: bytes.fromhex("842a4d37b036da6ab3c04331240e67d81746beb44f23ad79703e026705361956")
TxId = bytes


@dataclass(unsafe_hash=True)
class TrueData(PlutusData):
    """
    A Datum that represents True in Haskell implementations.
    It is thus used as an encoding for True in the ScriptContext.

    Example value: TrueData()
    """

    CONSTR_ID = 1


@dataclass(unsafe_hash=True)
class FalseData(PlutusData):
    """
    A Datum that represents False in Haskell implementations.
    It is thus used as an encoding for False in the ScriptContext.

    Example value: FalseData()
    """

    CONSTR_ID = 0


# A Datum that represents a boolean value in Haskell implementations.
# It is thus used as an encoding for booleans in the ScriptContext.
#
# Example value: TrueData()
BoolData = Union[TrueData, FalseData]


@dataclass(unsafe_hash=True)
class BoxedInt(PlutusData):
    """
    A boxed integer, used to represent an optional integer value
    """

    CONSTR_ID = 0
    value: int


@dataclass(unsafe_hash=True)
class NoValue(PlutusData):
    """
    An empty value (None case of Optional / Maybe)
    """

    CONSTR_ID = 1


Lovelace = int
OptionalInt = Union[BoxedInt, NoValue]
OptionalLovelace = OptionalInt


@dataclass(unsafe_hash=True)
class TxOutRef(PlutusData):
    """
    A reference to a transaction output (hash/id + index)
    """

    CONSTR_ID = 0

    id: TxId
    idx: int


# A public key hash, used to identify signatures provided by a wallet
# in aiken, this is called VerificationKeyHash
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

    CONSTR_ID = 0

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


MaybeScriptHash = Union[SomeScriptHash, NoScriptHash]

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

    CONSTR_ID = 0

    address: Address
    value: Value
    datum: OutputDatum
    reference_script: Union[NoScriptHash, SomeScriptHash]


@dataclass(unsafe_hash=True)
class TxInInfo(PlutusData):
    """
    The plutus representation of an transaction output, that is consumed by the transaction.
    """

    CONSTR_ID = 0

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


Certificate = Union[
    DCertDelegRegKey,
    DCertDelegDeRegKey,
    DCertDelegDelegate,
    DCertPoolRegister,
    DCertPoolRetire,
    DCertGenesis,
    DCertMir,
]


# POSIX time in milliseconds, typically originating from the Cardano node.
# Note that Python's `time.time()` provides seconds, so remember to multiply by 1000.
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
    Note: POSIX time is in milliseconds, while Python's time.time() provides seconds, so remember to multiply/divide by 1000 when interacting with off-chain code.
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
    Note: The transaction can be submitted at any point of time in the range.
    Deriving the actual submission time can be tricky. Best practices use only the upper or lower bound, depending on the use case.
    For example, if you accrue interest over time, use only the upper bound as the submission time, which is guaranteed to be after the actual submission time, but can be set tightly by the user to match the actual submission time.
    """

    CONSTR_ID = 0

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
class Withdrawing(PlutusData):
    """
    For scripts that validate reward withdrawals from a reward account.
    The argument identifies the target reward account.
    """

    CONSTR_ID = 2
    staking_credential: StakingCredential


@dataclass(unsafe_hash=True)
class ConstitutionalCommitteeMember(PlutusData):
    CONSTR_ID = 0
    credential: Credential


@dataclass(unsafe_hash=True)
class DelegateRepresentative(PlutusData):
    CONSTR_ID = 1
    credential: Credential


@dataclass(unsafe_hash=True)
class StakePool(PlutusData):
    CONSTR_ID = 2
    verification_key_hash: PubKeyHash


Voter = Union[ConstitutionalCommitteeMember, DelegateRepresentative, StakePool]


@dataclass(unsafe_hash=True)
class GovernanceActionId(PlutusData):
    CONSTR_ID = 0
    transaction: TxId
    # Note: is a non-negative index to the proposal
    proposal_procedure: int


@dataclass(unsafe_hash=True)
class VoteNo(PlutusData):
    CONSTR_ID = 0


@dataclass(unsafe_hash=True)
class VoteYes(PlutusData):
    CONSTR_ID = 1


@dataclass(unsafe_hash=True)
class VoteAbstain(PlutusData):
    CONSTR_ID = 2


Vote = Union[VoteNo, VoteYes, VoteAbstain]


@dataclass(unsafe_hash=True)
class SomeGovernanceActionId(PlutusData):
    """
    Indicates that there is an governance action id associated with this output, given in the first field
    """

    CONSTR_ID = 0
    governance_action_id: GovernanceActionId


@dataclass(unsafe_hash=True)
class NoGovernanceActionId(PlutusData):
    """
    Indicates that there is no governance action id associated with this output
    """

    CONSTR_ID = 1


# To convert these values to interpretable values,
# use the index -> value mapping from aiken
# https://github.com/aiken-lang/stdlib/blob/2.2.0/lib/cardano/governance/protocol_parameters.ak
# Explicit mapping functions may follow
ProtocolParametersUpdate = Dict[int, Datum]

MaybeGovernanceActionId = Union[SomeGovernanceActionId, NoGovernanceActionId]

# Below are Governance Actions (GAXXX)


@dataclass(unsafe_hash=True)
class GAProtocolParameters(PlutusData):
    CONSTR_ID = 0
    # The last governance action of type 'ProtocolParameters'. They must all form a chain.
    ancestor: MaybeGovernanceActionId
    # The new proposed protocol parameters. Only values set to `Some` are relevant.
    new_parameters: ProtocolParametersUpdate
    # The optional guardrails script defined in the constitution.
    # The script is executed by the ledger in addition to the hard-coded ledger rules.
    # It must pass for the new protocol parameters to be deemed valid.
    guardrails: Union[SomeScriptHash, NoScriptHash]


@dataclass(unsafe_hash=True)
class ProtocolVersion(PlutusData):
    CONSTR_ID = 0
    major: int
    minor: int


@dataclass(unsafe_hash=True)
class GAHardFork(PlutusData):
    CONSTR_ID = 1
    # The last governance action of type 'HardFork'. They must all form a chain.
    ancestor: MaybeGovernanceActionId
    # The new proposed version. A few rules apply to proposing new versions:
    #
    # - The `major` component, if incremented, must be exactly one more than the current.
    # - The `minor` component, if incremented, must be exactly one more than the current.
    # - If the `major` component is incremented, `minor` must be set to `0`.
    # - Neither `minor` nor `major` can be decremented.
    new_version: ProtocolVersion


@dataclass(unsafe_hash=True)
class GATreasuryWithdrawal(PlutusData):
    CONSTR_ID = 2
    #  A collection of beneficiaries, which can be plain verification key
    #  hashes or script hashes (e.g. DAO).
    beneficiaries: Dict[Credential, Lovelace]
    # The optional guardrails script defined in the constitution. The script
    # is executed by the ledger in addition to the hard-coded ledger rules.
    #
    # It must pass for the withdrawals to be authorized.
    guardrails: SomeScriptHash


@dataclass(unsafe_hash=True)
class GANoConfidence(PlutusData):
    CONSTR_ID = 3
    # The last governance action of type `NoConfidence` or `ConstitutionalCommittee`.
    # They must all form a chain.
    ancestor: MaybeGovernanceActionId


@dataclass(unsafe_hash=True)
class GAConstitutionalCommittee(PlutusData):
    CONSTR_ID = 4
    # The last governance action of type `NoConfidence` or `ConstitutionalCommittee`.
    # They must all / form a chain.
    ancestor: MaybeGovernanceActionId
    # Constitutional members to be removed.
    evicted_members: List[Credential]
    # Constitutional members to be added.
    # Int value is a "mandate", an epoch number after which constitutional committee member
    # mandate expires.
    added_members: Dict[Credential, int]
    # The new quorum value, as a ratio of a numerator and a denominator.
    # The quorum specifies the threshold of 'Yes' votes necessary for the constitutional committee to accept a proposal procedure.
    quorum: Fraction


@dataclass(unsafe_hash=True)
class Constitution(PlutusData):
    CONSTR_ID = 0
    # Guardrails for operations as a script
    guardrails: MaybeScriptHash


@dataclass(unsafe_hash=True)
class GANewConstitution(PlutusData):
    CONSTR_ID = 5
    # The last governance action of type `Constitution` or `ConstitutionalCommittee`.
    # They must all form a chain.
    ancestor: MaybeGovernanceActionId
    constitution: Constitution


@dataclass(unsafe_hash=True)
class GAInfo(PlutusData):
    # No effect on chain, only informative nature
    CONSTR_ID = 6


GovernanceAction = Union[
    GAProtocolParameters,
    GAHardFork,
    GATreasuryWithdrawal,
    GANoConfidence,
    GAConstitutionalCommittee,
    GANewConstitution,
    GAInfo,
]


@dataclass(unsafe_hash=True)
class ProposalProcedure(PlutusData):
    """
    Represents a proposal procedure in governance.
    """

    deposit: Lovelace
    return_address: Credential
    governance_action: GovernanceAction


@dataclass(unsafe_hash=True)
class Publishing(PlutusData):
    """
    Needed when delegating to a pool using stake credentials defined as a
    custom script. This purpose is also triggered when de-registering such
    stake credentials.

    The index is a 0-based index of the given `Certficate` in `certificates`.
    """

    CONSTR_ID = 3
    certificate_index: int
    certificate: Certificate


@dataclass(unsafe_hash=True)
class Voting(PlutusData):
    """
    Voting for a type of voter using a governance action id to vote
    yes / no / abstain inside a transaction.
    The voter is who is doing the governance action.
    """

    CONSTR_ID = 4
    voter: Voter


@dataclass(unsafe_hash=True)
class Proposing(PlutusData):
    """
    Used to propose a governance action.
    A 0-based index of the given `ProposalProcedure` in `proposal_procedures`.
    """

    CONSTR_ID = 5
    proposal_index: int
    proposal_procedure: ProposalProcedure


# The reason that this script is being invoked
ScriptPurpose = Union[Minting, Spending, Withdrawing, Publishing, Voting, Proposing]


@dataclass(unsafe_hash=True)
class TxInfo(PlutusData):
    """
    A complex agglomeration of everything that could be of interest to the executed script, regarding the transaction
    that invoked the script
    """

    CONSTR_ID = 0
    inputs: List[TxInInfo]
    reference_inputs: List[TxInInfo]
    outputs: List[TxOut]
    fee: Lovelace
    mint: Value
    certificates: List[Certificate]
    # NOTE: Withdrawals are ordered by ascending Credential. Yet, note that `Script` credentials are treated as **lower values** than `VerificationKey` credentials.
    withdrawals: Dict[StakingCredential, int]
    validity_range: POSIXTimeRange
    # NOTE: Redeemers are ordered by ascending ScriptPurpose.
    signatories: List[PubKeyHash]
    redeemers: Dict[ScriptPurpose, Redeemer]
    datums: Dict[DatumHash, Datum]
    id: TxId
    # NOTE: Votes are ordered by ascending Voter and GovernanceActionId. First constructor variants in a type are treated as lower indices; except for Credential where `Script` credentials are treated as **lower values** than `VerificationKey` credentials.
    votes: Dict[Voter, Dict[GovernanceActionId, Vote]]
    proposal_procedures: List[ProposalProcedure]
    current_treasury_amount: OptionalLovelace
    treasury_donation: OptionalLovelace


@dataclass(unsafe_hash=True)
class ScriptContext(PlutusData):
    """
    Auxiliary information about the transaction and reason for invocation of the called script.
    """

    CONSTR_ID = 0
    transaction: TxInfo
    redeemer: Redeemer
    purpose: ScriptPurpose
