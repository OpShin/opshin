from opshin.ledger.interval import *


@dataclass
class VestingParams(PlutusData):
    """
    Datum format
    source: the published, who can also reclaim the UTxO anytime (refund)
    beneficiary: the vesting beneficiary, who can claim the UTxO after the deadline
        if he pays the fee to the fee_address and the datum value ("info") is greater than the limit
    fee_address: the address where the fee must be paid
    fee: the fee amount which must be paid
    deadline: the vesting deadline
    limit: the minimum limit for the datum value which allows the UTxO to be claimed by the beneficiary
    """
    source: PubKeyHash
    beneficiary: PubKeyHash
    fee_address: bytes
    fee: int
    deadline: POSIXTime
    limit: int


@dataclass
class PublishParams(PlutusData):
    """
    Oracle datum format
    owner: publisher of the datum, who can also reclaim the UTxO after the deadline (refund)
    deadline:  the deadline after which the datum UTxO can be refunded
    info: the useful information in the oracle datum, an int in this case
    """
    owner: PubKeyHash
    deadline: POSIXTime
    info: int


@dataclass
class ClaimRedeemer(PlutusData):
    CONSTR_ID = 0
    pass


@dataclass
class RefundRedeemer(PlutusData):
    CONSTR_ID = 1
    pass


def validator(
        datum: VestingParams,
        redeemer: Union[ClaimRedeemer, RefundRedeemer],
        context: ScriptContext
) -> None:

    if isinstance(redeemer, ClaimRedeemer):
        """
        first check if the beneficiary signed the transaction 
        and if the transaction was submitted after the deadline
        """
        assert datum.beneficiary in context.tx_info.signatories, "Collect signature missing!"
        assert contains(make_from(datum.deadline), context.tx_info.valid_range), "TX submitted too early!"
        """
        check if the fee has been paid to the fee address
        """
        ff = False  # fee address found
        fp = False  # fee paid
        for item in context.tx_info.outputs:
            if datum.fee_address == item.address.payment_credential.credential_hash:
                ff = True
                if item.value.get(b'', {b'': 0}).get(b'', 0) >= datum.fee:
                    fp = True
        assert ff, "Fee address not found in outputs!"
        assert fp, "Fee too small!"
        """
        check if the datum.info from the reference input is greater than the datum.limit from the claimed UtxO
        """
        dc = False  # datum condition
        for ri in context.tx_info.reference_inputs:
            ris = ri.resolved.reference_script
            if isinstance(ris, NoScriptHash):
                rid = ri.resolved.datum
                if isinstance(rid, SomeOutputDatum):
                    oi: PublishParams = rid.datum  # oracle info
                    if oi.info > datum.limit:
                        dc = True
        assert dc, "Claim condition not met!"
    elif isinstance(redeemer, RefundRedeemer):
        assert datum.source in context.tx_info.signatories, "Refund signature missing!"
    else:
        assert False, "Wrong redeemer"
