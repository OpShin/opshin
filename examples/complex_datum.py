from eopsin.prelude import *


@dataclass()
class Deposit(PlutusData):
    CONSTR_ID = 0
    minimum_lp: int


@dataclass()
class Withdraw(PlutusData):
    CONSTR_ID = 1
    minimum_coin_a: int
    minimum_coin_b: int


OrderStep = Union[Deposit, Withdraw]

# inspired by https://github.com/MuesliSwapTeam/muesliswap-cardano-pool-contracts/blob/main/dex/src/MuesliSwapPools/BatchOrder/Types.hs
@dataclass()
class BatchOrder(PlutusData):
    sender: Address
    receiver: Address
    # If some property might be ommited, just Union with Nothing and check for the instance at runtime!
    # Make sure the property is a PlutusData type, if not, wrap it
    receiver_datum_hash: Union[Nothing, SomeDatumHash]
    order_step: OrderStep
    batcher_fee: int
    output_ada: int
    pool_nft_tokenname: TokenName
    script_version: bytes


# If some parameter might be ommited, just Union with Nothing and check for the instance at runtime!
def validator(d: Union[Nothing, BatchOrder]) -> bytes:
    if isinstance(d, BatchOrder):
        c = d.sender.payment_credential
        res = c.credential_hash
    elif isinstance(d, Nothing):
        res = b""
    # Throws a NameError if the instances don't match - this is fine, it means that the contract was not invoked correctly!
    return res
