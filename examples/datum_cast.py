from eopsin.prelude import *


# inspired by https://github.com/MuesliSwapTeam/muesliswap-cardano-pool-contracts/blob/main/dex/src/MuesliSwapPools/BatchOrder/Types.hs
@dataclass()
class BatchOrder(PlutusData):
    sender: Address
    receiver: Address
    receiver_datum_hash: Union[Nothing, SomeDatumHash]
    batcher_fee: int
    output_ada: int
    pool_nft_tokenname: TokenName
    script_version: bytes


def validator(d: Anything) -> bytes:
    # this casts the input to BatchOrder - in the type system! In the contract this is a no-op
    # this means that the contract never actually changes if the type fully matches!
    e: BatchOrder = d
    c = e.sender.credential
    if isinstance(c, PubKeyCredential):
        res = c.pubkeyhash
    return res
