"""
A simple AMM pool contract that allows users to add and remove liquidity and swap tokens.
DISCLAIMER: This is a simple example to demonstrate onchain based contract upgradeability and should not be used in production.
"""

from opshin.prelude import *
from opshin.ledger.interval import *
from opshin.std.fractions import *
from opshin.std.integrity import check_integrity

EMTPY_TOKENNAME_DICT: Dict[bytes, int] = {}
EMPTY_VALUE_DICT: Value = {}

ProposalId = int


@dataclass
class TallyResult(PlutusData):
    CONSTR_ID = 4
    winning_proposal: Anything
    proposal_id: ProposalId


def check_greater_or_equal_value(a: Value, b: Value) -> None:
    """
    Check that the value of a is greater or equal to the value of b, i.e. a >= b
    """
    for policy_id, tokens in b.items():
        for token_name, amount in tokens.items():
            assert (
                a.get(policy_id, {b"": 0}).get(token_name, 0) >= amount
            ), f"Value of {policy_id.hex()}.{token_name.hex()} is too low"


def check_mint_exactly_n_with_name(
    mint: Value, n: int, policy_id: PolicyId, required_token_name: TokenName
) -> None:
    """
    Check that exactly n token with the given name is minted
    from the given policy
    """
    assert mint[policy_id][required_token_name] == n, "Exactly n token must be minted"
    assert len(mint[policy_id]) == 1, "No other token must be minted"


def check_mint_exactly_nothing(
    mint: Value, policy_id: PolicyId, token_name: TokenName
) -> None:
    """
    Check that exactly no token with the given policy and name is minted
    """
    for pid, tokens in mint.items():
        if pid == policy_id:
            for tn, _ in tokens.items():
                assert tn != token_name, "No token of this name must be minted"


def merge_without_duplicates(a: List[bytes], b: List[bytes]) -> List[bytes]:
    """
    Merge two lists without duplicates
    Note: The cost of this is O(n^2), can we assume that the lists are small?
    Rough estimate allows 1000 bytes / 32 bytes per policy id ~ 31 policy ids
    However for token names no lower bound on the length is given, so we assume 1000 bytes / 1 byte per token name ~ 1000 token names
    """
    return [x for x in a if not x in b] + b


def _subtract_token_names(
    a: Dict[TokenName, int], b: Dict[TokenName, int]
) -> Dict[TokenName, int]:
    """
    Subtract b from a, return a - b
    """
    if not b:
        return a
    elif not a:
        return {tn_amount[0]: -tn_amount[1] for tn_amount in b.items()}
    return {
        tn: a.get(tn, 0) - b.get(tn, 0)
        for tn in merge_without_duplicates(a.keys(), b.keys())
    }


def subtract_value(a: Value, b: Value) -> Value:
    """
    Subtract b from a, return a - b
    """
    if not b:
        return a
    elif not a:
        return {
            pid_tokens[0]: {
                tn_amount[0]: -tn_amount[1] for tn_amount in pid_tokens[1].items()
            }
            for pid_tokens in b.items()
        }
    return {
        pid: _subtract_token_names(
            a.get(pid, EMTPY_TOKENNAME_DICT), b.get(pid, EMTPY_TOKENNAME_DICT)
        )
        for pid in merge_without_duplicates(a.keys(), b.keys())
    }


def _add_token_names(
    a: Dict[TokenName, int], b: Dict[TokenName, int]
) -> Dict[TokenName, int]:
    """
    Add b to a, return a + b
    """
    if not a:
        return b
    if not b:
        return a
    return {
        tn: a.get(tn, 0) + b.get(tn, 0)
        for tn in merge_without_duplicates(a.keys(), b.keys())
    }


def add_value(a: Value, b: Value) -> Value:
    """
    Add b to a, return a + b
    """
    if not a:
        return b
    if not b:
        return a
    return {
        pid: _add_token_names(
            a.get(pid, EMTPY_TOKENNAME_DICT), b.get(pid, EMTPY_TOKENNAME_DICT)
        )
        for pid in merge_without_duplicates(a.keys(), b.keys())
    }


def mul_fraction(a: Fraction, b: Fraction) -> Fraction:
    return Fraction(a.numerator * b.numerator, a.denominator * b.denominator)


def sub_fraction(a: Fraction, b: Fraction) -> Fraction:
    return Fraction(
        a.numerator * b.denominator - b.numerator * a.denominator,
        a.denominator * b.denominator,
    )


def floor_fraction(a: Fraction) -> int:
    return a.numerator // a.denominator


def amount_of_token_in_output(token: Token, output: TxOut) -> int:
    return output.value.get(token.policy_id, {b"": 0}).get(token.token_name, 0)


def amount_of_token_in_value(
    token: Token,
    value: Value,
) -> int:
    return value.get(token.policy_id, {b"": 0}).get(token.token_name, 0)


@dataclass
class ImmutablePoolParams(PlutusData):
    CONSTR_ID = 0
    token_a: Token
    token_b: Token
    pool_nft: Token
    pool_lp_token: Token


@dataclass
class UpgradeablePoolParams(PlutusData):
    CONSTR_ID = 0
    fee: Fraction
    auth_nft: Token
    license_policy_id: PolicyId
    last_applied_proposal_id: int


@dataclass
class PoolState(PlutusData):
    CONSTR_ID = 0
    im_pool_params: ImmutablePoolParams
    up_pool_params: UpgradeablePoolParams
    global_liquidity_tokens: int
    spent_for: Union[TxOutRef, Nothing]


@dataclass
class PoolUpgradeParams(PlutusData):
    """VOTE OUTCOME"""

    CONSTR_ID = 106
    # Set to specific token to upgrade only one, or Nothing to upgrade all
    old_pool_nft: Union[Token, Nothing]
    # Set to desired new parameters and address of pool
    # Set to Nothing to preserve old parameters
    new_pool_params: Union[UpgradeablePoolParams, Nothing]
    new_pool_address: Union[Address, Nothing]


def winning_tally_result(
    tally_input_index: int,
    auth_nft: Token,
    tx_info: TxInfo,
    last_applied_proposal_id: ProposalId,
    enforce_vote_ended: bool,
) -> TallyResult:
    """
    This ensures that the index points to a winning proposal
    """
    # Dummy implementation, replace with actual tally logic
    return TallyResult(
        winning_proposal=PoolUpgradeParams(
            old_pool_nft=Nothing(),
            new_pool_params=Nothing(),
            new_pool_address=Nothing(),
        ),
        proposal_id=last_applied_proposal_id + 1,
    )


def compare_upper_lower_bound(a: UpperBoundPOSIXTime, b: LowerBoundPOSIXTime) -> int:
    # a < b: 1
    # a == b: 0
    # a > b: -1
    result = compare_extended(a.limit, b.limit)
    if result == 0:
        a_closed = get_bool(a.closed)
        b_closed = get_bool(b.closed)
        if a_closed and b_closed:
            result = 0
        else:
            result = 1
    return result


def compare_lower_upper_bound(a: LowerBoundPOSIXTime, b: UpperBoundPOSIXTime) -> int:
    # a < b: 1
    # a == b: 0
    # a > b: -1
    result = compare_extended(a.limit, b.limit)
    if result == 0:
        a_closed = get_bool(a.closed)
        b_closed = get_bool(b.closed)
        if a_closed and b_closed:
            result = 0
        else:
            result = -1
    return result


def entirely_after(a: POSIXTimeRange, b: POSIXTimeRange) -> bool:
    """Returns whether all of a is after b. |---b---| |---a---|"""
    return compare_lower_upper_bound(a.lower_bound, b.upper_bound) == -1


def entirely_before(a: POSIXTimeRange, b: POSIXTimeRange) -> bool:
    """Returns whether all of a is before b. |---a---| |---b---|"""
    return compare_upper_lower_bound(a.upper_bound, b.lower_bound) == 1


def before_ext(a: POSIXTimeRange, b: ExtendedPOSIXTime) -> bool:
    """Returns whether all of a is before b. |---a---| b"""
    return (
        compare_upper_lower_bound(a.upper_bound, LowerBoundPOSIXTime(b, TrueData()))
        == 1
    )


def after_ext(a: POSIXTimeRange, b: ExtendedPOSIXTime) -> bool:
    """Returns whether all of a is after b. b |---a---|"""
    return (
        compare_upper_lower_bound(UpperBoundPOSIXTime(b, TrueData()), a.lower_bound)
        == 1
    )


def ext_after_ext(a: ExtendedPOSIXTime, b: ExtendedPOSIXTime) -> bool:
    """
    Check if a is after b, i.e b a
    """
    return compare_extended(a, b) == -1


@dataclass
class SwapAsset(PlutusData):
    CONSTR_ID = 1
    license_input_index: int
    pool_input_index: int
    pool_output_index: int
    swap_token: Token
    swap_token_amount: int


@dataclass
class AddLiquidity(PlutusData):
    CONSTR_ID = 2
    license_input_index: int
    pool_input_index: int
    pool_output_index: int
    deposit_token_a: int


@dataclass
class RemoveLiquidity(PlutusData):
    CONSTR_ID = 3
    license_input_index: int
    pool_input_index: int
    pool_output_index: int
    burn_liquidity_token: int


@dataclass
class PoolUpgrade(PlutusData):
    CONSTR_ID = 4
    pool_input_index: int
    pool_output_index: int
    tally_ref_index: int


PoolAction = Union[AddLiquidity, RemoveLiquidity, SwapAsset, PoolUpgrade]


def license_validity_from_name(license_name: TokenName) -> POSIXTime:
    """
    Extracts the validity time from a license name
    """
    return unsigned_int_from_bytes_big(license_name[16:32])


def check_valid_license_present(
    license_input_index: int, tx_info: TxInfo, license_policy_id: PolicyId
):
    """
    Checks that a valid license is present in the transaction
    """
    license_input = tx_info.inputs[license_input_index].resolved
    # note: no other licenses should be present in the input to ensure that this passes
    license_nft_name = license_input.value[license_policy_id].keys()[0]
    license_expiry_date = license_validity_from_name(license_nft_name)
    assert before_ext(
        tx_info.validity_range, FinitePOSIXTime(license_expiry_date)
    ), "License is expired"


def check_change_liquidity(
    datum: PoolState,
    redeemer: Union[AddLiquidity, RemoveLiquidity],
    context: ScriptContext,
    own_input_info: TxInInfo,
    own_output: TxOut,
) -> None:
    """
    Validates that the deposit of liquidity is done correctly
    """
    own_input = own_input_info.resolved

    # compute expected added liquidity
    if isinstance(redeemer, AddLiquidity):
        # Follows theorem 2 in https://github.com/runtimeverification/verified-smart-contracts/blob/uniswap/uniswap/x-y-k.pdf
        delta_token_a = redeemer.deposit_token_a
        assert delta_token_a > 0, "Liquidity change must be positive"

        pool_value_token_a = amount_of_token_in_value(
            datum.im_pool_params.token_a, own_input.value
        )
        pool_value_token_b = amount_of_token_in_value(
            datum.im_pool_params.token_b, own_input.value
        )
        alpha = Fraction(delta_token_a, pool_value_token_a)
        expected_deposit_token_a = delta_token_a
        expected_deposit_token_b = (
            floor_fraction(mul_fraction(alpha, Fraction(pool_value_token_b, 1))) + 1
        )
        expected_minted_lp_tokens = floor_fraction(
            mul_fraction(Fraction(datum.global_liquidity_tokens, 1), alpha)
        )
    else:
        # Follows definition 3 in https: // github.com / runtimeverification / verified - smart - contracts / blob / uniswap / uniswap / x - y - k.pdf
        delta_liquidity_token = redeemer.burn_liquidity_token
        assert delta_liquidity_token < 0, "Liquidity change must be negative"

        pool_value_token_a = amount_of_token_in_value(
            datum.im_pool_params.token_a, own_input.value
        )
        pool_value_token_b = amount_of_token_in_value(
            datum.im_pool_params.token_b, own_input.value
        )
        alpha = Fraction(delta_liquidity_token, datum.global_liquidity_tokens)
        expected_deposit_token_a = ceil_fraction(
            mul_fraction(alpha, Fraction(pool_value_token_a, 1))
        )
        expected_deposit_token_b = ceil_fraction(
            mul_fraction(alpha, Fraction(pool_value_token_b, 1))
        )
        expected_minted_lp_tokens = delta_liquidity_token

    # check addition of exactly the right amount of liquidity
    expected_new_global_liquidity_tokens = (
        datum.global_liquidity_tokens + expected_minted_lp_tokens
    )
    check_mint_exactly_n_with_name(
        context.transaction.mint,
        expected_minted_lp_tokens,
        datum.im_pool_params.pool_lp_token.policy_id,
        datum.im_pool_params.pool_lp_token.token_name,
    )

    previous_value = own_input.value
    new_value = own_output.value
    expected_new_value = add_value(
        previous_value,
        {
            datum.im_pool_params.token_a.policy_id: {
                datum.im_pool_params.token_a.token_name: expected_deposit_token_a
            },
            datum.im_pool_params.token_b.policy_id: {
                datum.im_pool_params.token_b.token_name: expected_deposit_token_b
            },
        },
    )
    check_greater_or_equal_value(new_value, expected_new_value)

    # check that the new pool state is correct
    assert (
        own_output.address == own_input.address
    ), "Liquidity change must not change address"
    assert own_output.datum == SomeOutputDatum(
        PoolState(
            datum.im_pool_params,
            datum.up_pool_params,
            expected_new_global_liquidity_tokens,
            own_input_info.out_ref,
        )
    ), "Pool state must reflect new liquidity"


def check_swap(
    datum: PoolState,
    redeemer: SwapAsset,
    context: ScriptContext,
    own_input_info: TxInInfo,
    own_output: TxOut,
) -> None:
    """
    Validates that the swapping of tokens is done correctly
    """
    own_input = own_input_info.resolved

    # compute expected added liquidity
    delta_token = redeemer.swap_token_amount
    assert delta_token > 0, "Swap amount must be positive"

    pool_value_token_a = amount_of_token_in_value(
        datum.im_pool_params.token_a, own_input.value
    )
    pool_value_token_b = amount_of_token_in_value(
        datum.im_pool_params.token_b, own_input.value
    )
    if redeemer.swap_token == datum.im_pool_params.token_a:
        # need to deposit token a plus pool fee
        expected_change_token_a = delta_token + ceil_fraction(
            mul_fraction(datum.up_pool_params.fee, Fraction(delta_token, 1))
        )
        expected_change_token_b = -floor_fraction(
            sub_fraction(
                Fraction(pool_value_token_b, 1),
                Fraction(
                    pool_value_token_a * pool_value_token_b,
                    pool_value_token_a + delta_token,
                ),
            )
        )
    else:
        # need to deposit token b plus pool fee
        expected_change_token_b = delta_token + ceil_fraction(
            mul_fraction(datum.up_pool_params.fee, Fraction(delta_token, 1))
        )
        expected_change_token_a = -floor_fraction(
            sub_fraction(
                Fraction(pool_value_token_a, 1),
                Fraction(
                    pool_value_token_a * pool_value_token_b,
                    pool_value_token_b + delta_token,
                ),
            )
        )

    # no liquidity tokens must be minted
    check_mint_exactly_nothing(
        context.transaction.mint,
        datum.im_pool_params.pool_lp_token.policy_id,
        datum.im_pool_params.pool_lp_token.token_name,
    )

    previous_value = own_input.value
    new_value = own_output.value
    expected_new_value = add_value(
        previous_value,
        {
            datum.im_pool_params.token_a.policy_id: {
                datum.im_pool_params.token_a.token_name: expected_change_token_a
            },
            datum.im_pool_params.token_b.policy_id: {
                datum.im_pool_params.token_b.token_name: expected_change_token_b
            },
        },
    )
    check_greater_or_equal_value(new_value, expected_new_value)

    # check that the new pool state is correct
    assert (
        own_output.address == own_input.address
    ), "Liquidity change must not change address"
    assert own_output.datum == SomeOutputDatum(
        PoolState(
            datum.im_pool_params,
            datum.up_pool_params,
            datum.global_liquidity_tokens,
            own_input_info.out_ref,
        )
    ), "Pool state must not change except for output reference"


def check_upgrade(
    datum: PoolState,
    redeemer: PoolUpgrade,
    context: ScriptContext,
    own_input_info: TxInInfo,
    own_output: TxOut,
) -> None:
    """
    Validates that a tally justifies the upgrade and that the upgrade is done correctly
    """
    # no liquidity tokens must be minted
    check_mint_exactly_nothing(
        context.transaction.mint,
        datum.im_pool_params.pool_lp_token.policy_id,
        datum.im_pool_params.pool_lp_token.token_name,
    )
    # obtain the tally result that justifies the payout
    tally_result = winning_tally_result(
        redeemer.tally_ref_index,
        datum.up_pool_params.auth_nft,
        context.transaction,
        datum.up_pool_params.last_applied_proposal_id,
        True,
    )
    pool_upgrade_params: PoolUpgradeParams = tally_result.winning_proposal
    # check that the winning proposal is actually a pool upgrade
    check_integrity(pool_upgrade_params)

    # check that this specific pool is being upgraded
    raw_old_pool_nft = pool_upgrade_params.old_pool_nft
    if isinstance(raw_old_pool_nft, Token):
        assert (
            raw_old_pool_nft == datum.im_pool_params.pool_nft
        ), "Old pool nft does not match"
    else:
        pass  # upgrade all pools

    # check that the new pool state is correct
    raw_new_pool_params = pool_upgrade_params.new_pool_params
    if isinstance(raw_new_pool_params, UpgradeablePoolParams):
        new_pool_params = raw_new_pool_params
        assert (
            new_pool_params.last_applied_proposal_id == tally_result.proposal_id
        ), "Last applied proposal id must match the proposal id of the tally"
    else:
        # preserve old parameters except for the proposal id
        new_pool_params = UpgradeablePoolParams(
            datum.up_pool_params.fee,
            datum.up_pool_params.auth_nft,
            datum.up_pool_params.license_policy_id,
            tally_result.proposal_id,
        )
    raw_new_pool_address = pool_upgrade_params.new_pool_address
    if isinstance(raw_new_pool_address, Address):
        new_pool_address = raw_new_pool_address
    else:
        new_pool_address = own_output.address
    assert own_output.address == new_pool_address, "New pool address is incorrect"
    assert own_output.datum == SomeOutputDatum(
        PoolState(
            datum.im_pool_params,
            new_pool_params,
            datum.global_liquidity_tokens,
            own_input_info.out_ref,
        )
    ), "Pool params must match new pool params"
    check_greater_or_equal_value(
        own_output.value, own_input_info.resolved.value
    ), "Value must not decrease in upgrade"


def get_minting_purpose(context: ScriptContext) -> Minting:
    purpose = context.purpose
    assert isinstance(purpose, Minting)
    return purpose


def get_spending_purpose(context: ScriptContext) -> Spending:
    purpose = context.purpose
    assert isinstance(purpose, Spending)
    return purpose


def validator(context: ScriptContext) -> None:
    """
    Validates that the pool is spent correctly
    DISCLAIMER: This is a simple example to demonstrate onchain based contract upgradeability and should not be used in production.
    """
    purpose = get_spending_purpose(context)
    redeemer: PoolAction = context.redeemer
    check_integrity(redeemer)
    datum: PoolState = own_datum_unsafe(context)
    check_integrity(datum)
    own_input_info = context.transaction.inputs[redeemer.pool_input_index]
    assert (
        own_input_info.out_ref == purpose.tx_out_ref
    ), "Index of own input does not match purpose"

    own_output = context.transaction.outputs[redeemer.pool_output_index]
    if isinstance(redeemer, AddLiquidity) or isinstance(redeemer, RemoveLiquidity):
        check_valid_license_present(
            redeemer.license_input_index,
            context.transaction,
            datum.up_pool_params.license_policy_id,
        )
        check_change_liquidity(datum, redeemer, context, own_input_info, own_output)
    elif isinstance(redeemer, SwapAsset):
        check_valid_license_present(
            redeemer.license_input_index,
            context.transaction,
            datum.up_pool_params.license_policy_id,
        )
        check_swap(datum, redeemer, context, own_input_info, own_output)
    elif isinstance(redeemer, PoolUpgrade):
        check_upgrade(datum, redeemer, context, own_input_info, own_output)
    else:
        assert False, "Unknown redeemer"
