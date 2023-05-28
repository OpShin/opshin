from opshin.ledger.interval import *


@dataclass
class PublishParams(PlutusData):
    """
    Datum format
    owner: publisher of the datum, who can also reclaim the UTxO after the deadline (refund)
    deadline:  the deadline after which the datum UTxO can be refunded
    info: the useful information in the oracle datum, an int in this case
    """

    owner: PubKeyHash
    deadline: POSIXTime
    info: int


@dataclass
class RefundRedeemer(PlutusData):
    pass


def validator(
    datum: PublishParams, redeemer: RefundRedeemer, context: ScriptContext
) -> None:
    assert contains(
        make_from(datum.deadline), context.tx_info.valid_range
    ), "TX submitted too early!"
    assert datum.owner in context.tx_info.signatories, "Refund signature missing!"
