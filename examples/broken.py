from opshin.prelude import *


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


def validator(d: Anything, r: Anything) -> bytes:
    # this casts the input to BatchOrder - in the type system! In the contract this is a no-op
    if "s" == 4:
        e: BatchOrder = d
        c = e.sender.payment_credential
    return b""
