from eopsin.prelude import *


class Deposit(PlutusData):
    minimum_lp: int


class Withdraw(PlutusData):
    minimum_coin_a: int
    minimum_coin_b: int


OrderStep = Union[Deposit, Withdraw]

# inspired by https://github.com/MuesliSwapTeam/muesliswap-cardano-pool-contracts/blob/main/dex/src/MuesliSwapPools/BatchOrder/Types.hs
class BatchOrder(PlutusData):
    sender: Address
    receiver: Address
    receiver_datum_hash: Optional[DatumHash]
    order_step: OrderStep
    batcher_fee: int
    output_ada: int
    pool_nft_tokenname: TokenName
    script_version: bytes


def validator(d: BatchOrder) -> bytes:
    c = d.sender.credential
    res = b""
    if isinstance(c, PubKeyCredential):
        res = c.pubkeyhash
    return res
