#!opshin
from opshin.prelude import *


def has_nft(
    pool_nft_cs: PolicyId, pool_nft_tn: TokenName, tx_in_info: TxInInfo
) -> bool:
    return tx_in_info.resolved.value[pool_nft_cs][pool_nft_tn] == 1


def spends_pool_nft(
    inputs: List[TxInInfo], pool_nft_cs: PolicyId, pool_nft_tn: TokenName
) -> bool:
    for tx_in_info in inputs:
        if has_nft(pool_nft_cs, pool_nft_tn, tx_in_info):
            return True
    return False


def validator(pool_nft_cs_raw: Anything, context: ScriptContext) -> None:
    pool_nft_cs: PolicyId = pool_nft_cs_raw
    tx = context.transaction
    purpose = context.purpose
    if isinstance(purpose, Minting):
        own_symbol = purpose.policy_id
    else:
        assert False, "Invalid purpose"

    minted_names = tx.mint[own_symbol].keys()
    for minted_lp_name in minted_names:
        assert spends_pool_nft(tx.inputs, pool_nft_cs, minted_lp_name)
