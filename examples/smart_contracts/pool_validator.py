#!opshin
from opshin.prelude import *


@dataclass()
class AssetClass(PlutusData):
    CONSTR_ID = 0
    symbol: PolicyId
    name: TokenName


DexRedeemerSwap: int = 0
DexRedeemerDepositLiquidity: int = 1
DexRedeemerWithdrawLiquidity: int = 2


def quantity_of_asset(value: Value, asset_class: AssetClass) -> int:
    return value[asset_class.symbol][asset_class.name]


def quantity_of(value: Value, symbol: PolicyId, name: TokenName) -> int:
    if symbol in value.keys():
        return value[symbol].get(name, 0)
    else:
        return 0


def get_diff(new: int, old: int) -> int:
    if new - old < 0:
        return 0
    else:
        return new - old


fee_den: int = 1000


def check_swap(
    fee_num: int,
    old_a: int,
    old_b: int,
    new_a: int,
    new_b: int,
) -> bool:
    return fee_den * fee_den * old_a * old_b <= (
        new_a * fee_den - get_diff(new_a, old_a) * fee_num
    ) * (new_b * fee_den - get_diff(new_b, old_b) * fee_num)


def find_own_output(outputs: List[TxOut], pool_nft: AssetClass) -> TxOut:
    for output in outputs:
        if quantity_of_asset(output.value, pool_nft) == 1:
            return output
    assert False, "Missing own output"
    return outputs[0]


def validator(context: ScriptContext) -> None:
    tx = context.transaction
    purpose = context.purpose
    if isinstance(purpose, Spending):
        own_input = own_spent_utxo(tx.inputs, purpose)
    else:
        assert False, "Invalid purpose"

    redeemer: int = context.redeemer
    input_datum_raw: List[Anything] = resolve_datum_unsafe(own_input, tx)
    (
        token_a_raw,
        token_b_raw,
        pool_nft_raw,
        lp_token_raw,
        minted_lp_tokens_raw,
        swap_fee_raw,
    ) = input_datum_raw
    token_a: AssetClass = token_a_raw
    token_b: AssetClass = token_b_raw
    pool_nft: AssetClass = pool_nft_raw
    lp_token: PolicyId = lp_token_raw
    minted_lp_tokens: int = minted_lp_tokens_raw
    swap_fee: int = swap_fee_raw

    own_output = find_own_output(tx.outputs, pool_nft)
    new_minted_lp = quantity_of(tx.mint, lp_token, pool_nft.name)

    in_a_amount = quantity_of_asset(own_input.value, token_a)
    in_b_amount = quantity_of_asset(own_input.value, token_b)

    out_a_amount = quantity_of_asset(own_output.value, token_a)
    out_b_amount = quantity_of_asset(own_output.value, token_b)

    out_datum_some = own_output.datum
    if isinstance(out_datum_some, SomeOutputDatum):
        out_datum_raw: List[Anything] = out_datum_some.datum
    else:
        assert False, "Missing inline output datum"
    (
        out_token_a_raw,
        out_token_b_raw,
        out_pool_nft_raw,
        out_lp_token_raw,
        out_minted_lp_tokens_raw,
        out_swap_fee_raw,
    ) = out_datum_raw
    out_token_a: AssetClass = out_token_a_raw
    out_token_b: AssetClass = out_token_b_raw
    out_pool_nft: AssetClass = out_pool_nft_raw
    out_lp_token: PolicyId = out_lp_token_raw
    out_minted_lp_tokens: int = out_minted_lp_tokens_raw
    out_swap_fee: int = out_swap_fee_raw

    assert quantity_of_asset(own_input.value, pool_nft) == 1
    own_output_reference_script = own_output.reference_script
    assert isinstance(own_output_reference_script, NoScriptHash)
    assert token_a == out_token_a
    assert token_b == out_token_b
    assert pool_nft == out_pool_nft
    assert lp_token == out_lp_token
    assert swap_fee == out_swap_fee

    if redeemer == DexRedeemerDepositLiquidity:
        assert minted_lp_tokens + new_minted_lp == out_minted_lp_tokens
        assert new_minted_lp > 0
        assert (
            out_minted_lp_tokens * out_minted_lp_tokens <= out_a_amount * out_b_amount
        )
    elif redeemer == DexRedeemerWithdrawLiquidity:
        assert minted_lp_tokens + new_minted_lp == out_minted_lp_tokens
        assert new_minted_lp < 0
        assert (
            out_minted_lp_tokens * out_minted_lp_tokens <= out_a_amount * out_b_amount
        )
    elif redeemer == DexRedeemerSwap:
        assert minted_lp_tokens == out_minted_lp_tokens
        assert new_minted_lp == 0
        assert check_swap(
            swap_fee,
            in_a_amount,
            in_b_amount,
            out_a_amount,
            out_b_amount,
        )
    else:
        assert False, "Invalid redeemer"
