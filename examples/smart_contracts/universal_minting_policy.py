from eopsin.prelude import *


@dataclass()
class Mint(PlutusData):
    CONSTR_ID = 0
    ref: TxInInfo


@dataclass()
class Burn(PlutusData):
    CONSTR_ID = 1


def validator_template(
    dn: int, prec_NFT: TokenName, redeemer: Union[Mint, Burn], ctx: ScriptContext
) -> None:
    purpose = ctx.purpose
    if isinstance(purpose, Minting):
        cs = purpose.policy_id
        own_mints = ctx.tx_info.mint.get(cs, {b"": 0})

        if isinstance(redeemer, Mint):
            token_name_tail = sha256(
                redeemer.ref.out_ref.id + bytes([redeemer.ref.out_ref.idx])
            ).digest()[dn:]

            # check reference UTxO is actually consumed
            assert redeemer.ref in ctx.tx_info.inputs, "Referenced UTxO not consumed"

            prec_NFT_mint = own_mints.get(prec_NFT, 0)

            # check names of minted tokens end with tail
            for name in own_mints.keys():
                assert name[dn:] == token_name_tail, "Wrong tokenname"

            # check correct minting amounts for tokens
            for amount in own_mints.values():
                assert amount == 1, "Wrong token amount"
                assert (
                    prec_NFT == b"" or prec_NFT_mint == amount
                ), "OwnNFT should be minted"
        elif isinstance(redeemer, Burn):
            for amount in own_mints.values():
                assert amount == -1, "Own currency needs to be burnt"
        else:
            assert False, "Wrong redeemer passed in"
    else:
        assert False, "Purpose of mint call must be minting"


SLICED = 1
PREC_NFT = b""


def validator(redeemer: Union[Mint, Burn], ctx: ScriptContext) -> None:
    return validator_template(SLICED, PREC_NFT, redeemer, ctx)
