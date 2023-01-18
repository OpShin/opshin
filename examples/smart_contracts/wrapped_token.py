from eopsin.prelude import *

TOKEN_POLICYID = b"\x8a\x1c\xfa\xe2\x13h\xb8\xbe\xbb\xbe\xd9\x80\x0f\xec0N\x95\xcc\xe3\x9a*W\xdc5\xe2\xe3\xeb\xaa"
TOKEN_NAME = b"MILK"
WRAPPING_FACTOR = 1000000

TOKEN = Token(TOKEN_POLICYID, TOKEN_NAME)


def all_utxos_from_address(txins: List[TxInInfo], address: Address) -> List[TxInInfo]:
    filtered_txins = []
    for txi in txins:
        if txi.resolved.address == address:
            filtered_txins += [txi]
    return filtered_txins


def all_tokens_unlocked_from_address(
    txins: List[TxInInfo], address: Address, token: Token
) -> int:
    res = 0
    for txi in txins:
        if txi.resolved.address == address:
            res += txi.resolved.value[token.policy_id][token.token_name]
    return res


@dataclass()
class SomeTxOut(PlutusData):
    CONSTR_ID = 1
    tx_out: TxOut


def own_spent_utxo(txins: List[TxInInfo], p: Spending) -> Union[Nothing, SomeTxOut]:
    res = Nothing
    for txi in txins:
        if txi.out_ref == p.tx_out_ref:
            res = SomeTxOut(txi.resolved)
    return res


@dataclass()
class SomePolicyId(PlutusData):
    CONSTR_ID = 1
    policy_id: PolicyId


def own_policy_id(own_spent_utxo: TxOut) -> Union[Nothing, SomePolicyId]:
    cred = own_spent_utxo.address.credential
    res = Nothing
    if isinstance(cred, ScriptCredential):
        res = SomePolicyId(cred.validator_hash)
    return res


def own_address(own_policy_id: PolicyId) -> Address:
    return Address(ScriptCredential(own_policy_id), Nothing)


def all_tokens_locked_at_address(
    txouts: List[TxOut], address: Address, token: Token
) -> int:
    res = 0
    for txo in txouts:
        if txo.address == address:
            res += txo.value[token.policy_id][token.token_name]
    return res


def validator(_datum: None, _redeemer: None, ctx: ScriptContext) -> None:
    purpose = ctx.purpose
    if isinstance(purpose, Minting):
        own_addr = own_address(purpose.policy_id)
        all_locked = all_tokens_locked_at_address(ctx.tx_info.outputs, own_addr, TOKEN)
        all_minted = ctx.tx_info.mint[purpose.policy_id][TOKEN_NAME]
        if all_minted < 0:
            # negative mint indicates burning. reproduce check that spending script does
            all_unlocked = all_tokens_unlocked_from_address(
                ctx.tx_info.inputs, own_addr, TOKEN
            )
            assert (
                all_unlocked * WRAPPING_FACTOR
            ) == -all_minted, "Wrong amount of tokens burnt"
        else:
            assert (
                all_locked * WRAPPING_FACTOR
            ) == all_minted, "Wrong amount of tokens minted"
    elif isinstance(purpose, Spending):
        # whenever something is unlocked from the contract, the spending purpose will be triggered
        own_utxo = own_spent_utxo(ctx.tx_info.inputs, purpose)
        if isinstance(own_utxo, SomeTxOut):
            pid = own_policy_id(own_utxo.tx_out)
            if isinstance(pid, SomePolicyId):
                all_unlocked = all_tokens_unlocked_from_address(
                    ctx.tx_info.inputs, own_utxo.tx_out.address, TOKEN
                )
                all_burned = ctx.tx_info.mint[pid.policy_id][TOKEN_NAME]
                assert (
                    all_unlocked * WRAPPING_FACTOR
                ) == -all_burned, "Wrong amount of tokens burnt"
            else:
                assert False, "Could not determine own policy id"
        else:
            assert False, "Could not determine spent utxo"
    assert False, "Incorrect spending purpose given"
