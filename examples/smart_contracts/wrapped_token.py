#!opshin
from opshin.prelude import *


@dataclass
class Empty(PlutusData):
    CONSTR_ID = 0
    pass


def all_tokens_unlocked_from_contract_address(
    txins: List[TxInInfo], address: Address, token: Token
) -> int:
    # generally always iterate over all inputs to avoid double spending
    res = 0
    for txi in txins:
        if txi.resolved.address == address:
            res += txi.resolved.value.get(token.policy_id, {b"": 0}).get(
                token.token_name, 0
            )
    return res


def own_spent_utxo(txins: List[TxInInfo], p: Spending) -> TxOut:
    # obtain the resolved txout that is going to be spent from this contract address
    for txi in txins:
        if txi.out_ref == p.tx_out_ref:
            own_txout = txi.resolved
    # This throws a name error if the txout was not found
    return own_txout


def own_policy_id(own_spent_utxo: TxOut) -> PolicyId:
    # obtain the policy id for which this contract can validate minting/burning
    cred = own_spent_utxo.address.payment_credential
    if isinstance(cred, ScriptCredential):
        policy_id = cred.credential_hash
    # This throws a name error if the credential is not a ScriptCredential instance
    return policy_id


def own_address(own_policy_id: PolicyId) -> Address:
    return Address(ScriptCredential(own_policy_id), NoStakingCredential())


def all_tokens_locked_at_contract_address(
    txouts: List[TxOut], address: Address, token: Token
) -> int:
    res = 0
    for txo in txouts:
        if txo.address == address:
            res += txo.value.get(token.policy_id, {b"": 0}).get(token.token_name, 0)
            # enforce a small inlined datum
            assert txo.datum == SomeOutputDatum(
                b""
            ), f"Does not attach correct datum to script output, got {txo.datum} but expected {b''}"
    return res


# this is a parameterized contract. The first three arguments are
# parameters controlling which token is to be wrapped and how many decimal places to add
# compile the contract as follows to obtain the parameterized contract (for preprod milk)
#
# $ opshin build spending examples/smart_contracts/wrapped_token.py '{"bytes": "ae810731b5d21c0d182d89c60a1eff7095dffd1c0dce8707a8611099"}' '{"bytes": "4d494c4b"}' '{"int": 1000000}'
@dataclass()
class Contract:
    token_policy_id: bytes
    token_name: bytes
    wrapping_factor: int

    def validate_wrapping(
        self, own_addr: Address, own_pid: PolicyId, ctx: ScriptContext
    ) -> None:
        token = Token(self.token_policy_id, self.token_name)
        all_locked = all_tokens_locked_at_contract_address(
            ctx.transaction.outputs, own_addr, token
        )
        all_unlocked = all_tokens_unlocked_from_contract_address(
            ctx.transaction.inputs, own_addr, token
        )
        all_minted = ctx.transaction.mint.get(own_pid, {b"": 0}).get(
            b"w" + self.token_name, 0
        )
        print(f"unlocked from contract: {all_unlocked}")
        print(f"locked at contract: {all_locked}")
        print(f"minted: {all_minted}")
        assert (
            (all_locked - all_unlocked) * self.wrapping_factor
        ) == all_minted, f"Wrong amount of tokens minted, difference: {(all_locked - all_unlocked) * self.wrapping_factor - all_minted}"

    def mint(self, _redeemer: Anything, ctx: ScriptContext) -> None:
        purpose = ctx.purpose
        assert isinstance(purpose, Minting), "Incorrect purpose given"
        # whenever tokens should be burned/minted, the minting purpose will be triggered
        self.validate_wrapping(own_address(purpose.policy_id), purpose.policy_id, ctx)

    def spend(self, _redeemer: Anything, ctx: ScriptContext) -> None:
        purpose = ctx.purpose
        assert isinstance(purpose, Spending), "Incorrect purpose given"
        # whenever something is unlocked from the contract, the spending purpose will be triggered
        own_utxo = own_spent_utxo(ctx.transaction.inputs, purpose)
        self.validate_wrapping(own_utxo.address, own_policy_id(own_utxo), ctx)
