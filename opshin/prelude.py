from hashlib import sha256, sha3_256, blake2b
from opshin.ledger.api_v2 import *


@dataclass(unsafe_hash=True)
class Token(PlutusData):
    """
    A token, represented by policy id and token name
    """

    policy_id: PolicyId
    token_name: TokenName


# Used to indicate that this contract does not expect a redeemer
NoRedeemer = Nothing

### Optimized methods for handling tokens at addresses


def all_tokens_unlocked_from_address(
    txins: List[TxInInfo], address: Address, token: Token
) -> int:
    """Returns how many tokens of specified type are unlocked from given address"""
    return sum(
        [
            txi.resolved.value.get(token.policy_id, {b"": 0}).get(token.token_name, 0)
            for txi in txins
            if txi.resolved.address == address
        ]
    )


def all_tokens_locked_at_address_with_datum(
    txouts: List[TxOut], address: Address, token: Token, output_datum: OutputDatum
) -> int:
    """Returns how many tokens of specified type are locked at then given address with the specified datum"""
    return sum(
        [
            txo.value.get(token.policy_id, {b"": 0}).get(token.token_name, 0)
            for txo in txouts
            if txo.address == address and txo.datum == output_datum
        ]
    )


def all_tokens_locked_at_address(
    txouts: List[TxOut], address: Address, token: Token
) -> int:
    """Returns how many tokens of specified type are locked at the given address"""
    return sum(
        [
            txo.value.get(token.policy_id, {b"": 0}).get(token.token_name, 0)
            for txo in txouts
            if txo.address == address
        ]
    )


def resolve_spent_utxo(txins: List[TxInInfo], p: Spending) -> TxOut:
    """Returns the UTxO whose spending should be validated"""
    return [txi.resolved for txi in txins if txi.out_ref == p.tx_out_ref][0]
