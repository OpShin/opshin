#!opshin
from opshin.prelude import *
from opshin.std.builtins import *


NftMarketplaceRedeemer = int
NftMarketplaceRedeemerBuy = 0
NftMarketplaceRedeemerCancel = 1

NftMarketplaceDatum = List[Anything]


def has_valid_payment(
    outputs: List[TxOut], address: Address, price: Value, own_input: TxOutRef
) -> bool:
    own_input_data: Anything = own_input
    price_data: Anything = price
    for output in outputs:
        if output.address == address and equals_data(output.value, price_data):
            output_datum = output.datum
            if isinstance(output_datum, SomeOutputDatum) and equals_data(
                output_datum.datum, own_input_data
            ):
                return True
    return False


def validator(context: ScriptContext) -> None:
    tx = context.transaction
    purpose = context.purpose
    if isinstance(purpose, Spending):
        own_input = purpose.tx_out_ref
    else:
        assert False, "Invalid purpose"

    datum: NftMarketplaceDatum = own_datum_unsafe(context)
    redeemer: NftMarketplaceRedeemer = context.redeemer
    assert len(datum) == 3, "Invalid datum"
    price_raw, address_raw, cancel_key_raw = datum
    price: Value = price_raw
    address: Address = address_raw
    cancel_key: PubKeyHash = cancel_key_raw

    if redeemer == NftMarketplaceRedeemerBuy:
        assert has_valid_payment(tx.outputs, address, price, own_input)
    elif redeemer == NftMarketplaceRedeemerCancel:
        is_signed = cancel_key in tx.signatories
        assert is_signed
    else:
        assert False, "Invalid redeemer"
