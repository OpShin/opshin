#!opshin
from opshin.prelude import *


def derive_nft_name(ref: TxOutRef) -> TokenName:
    assert ref.idx < 256, "TxOutRef idx too large"
    return ref.id + bytes([ref.idx])


def validator(context: ScriptContext) -> None:
    purpose = context.purpose
    if isinstance(purpose, Minting):
        own_symbol = purpose.policy_id
    else:
        assert False, "Invalid purpose"

    initial_spend: TxOutRef = context.redeemer
    minted_names = context.transaction.mint[own_symbol].items()
    assert len(minted_names) == 1, "Minted ore than one NFT name"
    minted_name_entry = minted_names[0]
    minted_nft_name, minted_nft_amount = minted_name_entry

    assert minted_nft_amount == 1, "Minted one NFT"
    assert minted_nft_name == derive_nft_name(
        initial_spend
    ), "Minted NFT name does not match derived name"

    assert any(
        [initial_spend == inp.out_ref for inp in context.transaction.inputs]
    ), "Initial spent is not spent"
