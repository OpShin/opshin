from opshin.prelude import *


@dataclass()
class Listing(PlutusData):
    # Price of the listing in lovelace
    price: int
    # the owner of the listed object
    vendor: Address
    # whoever is allowed to withdraw the listing
    owner: PubKeyHash


@dataclass()
class Buy(PlutusData):
    # Redeemer to buy the listed values
    CONSTR_ID = 0


@dataclass()
class Unlist(PlutusData):
    # Redeemer to unlist the values
    CONSTR_ID = 1


ListingAction = Union[Buy, Unlist]


def check_paid(txouts: List[TxOut], addr: Address, price: int) -> None:
    """Check that the correct amount has been paid to the vendor (or more)"""
    res = False
    for txo in txouts:
        if txo.value.get(b"", {b"": 0}).get(b"", 0) >= price and txo.address == addr:
            res = True
    assert res, "Did not send required amount of lovelace to vendor"


def check_single_utxo_spent(txins: List[TxInInfo], addr: Address) -> None:
    """To prevent double spending, count how many UTxOs are unlocked from the contract address"""
    count = 0
    for txi in txins:
        if txi.resolved.address == addr:
            count += 1
    assert count == 1, "Only 1 contract utxo allowed"


def check_owner_signed(signatories: List[PubKeyHash], owner: PubKeyHash) -> None:
    assert owner in signatories, "Owner did not sign transaction"


def validator(datum: Listing, redeemer: ListingAction, context: ScriptContext) -> None:
    purpose = context.purpose
    tx_info = context.tx_info
    if isinstance(purpose, Spending):
        own_utxo = resolve_spent_utxo(tx_info.inputs, purpose)
        own_addr = own_utxo.address
    else:
        assert False, "Wrong script purpose"

    check_single_utxo_spent(tx_info.inputs, own_addr)
    if isinstance(redeemer, Buy):
        check_paid(tx_info.outputs, datum.vendor, datum.price)
    elif isinstance(redeemer, Unlist):
        check_owner_signed(tx_info.signatories, datum.owner)
    else:
        assert False, "Wrong redeemer"
