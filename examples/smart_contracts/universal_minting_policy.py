from eopsin.prelude import *


@dataclass()
class Mint(PlutusData):
    CONSTR_ID = 0
    ref: TxInInfo


@dataclass()
class Burn(PlutusData):
    CONSTR_ID = 1


# Set parameter before re-compiling
# eopsin contracts don't natively support parameterization
precNFT = b""


def validator(dn: int, redeemer: Union[Mint, Burn], ctx: ScriptContext) -> None:
    purpose = ctx.purpose
    if isinstance(purpose, Minting):
        cs = purpose.currency_symbol

        if isinstance(redeemer, Mint):
            tokenNameTail = hash(
                redeemer.ref.out_ref.id + bytes([redeemer.ref.out_ref.idx])
            )[dn:]
            assert redeemer.ref in ctx.tx_info.inputs, "Reference UTxO not consumed"
            mintPrecNFT = ctx.tx_info.mint[precNFT]
            for name, amount in ctx.tx_info.mint[cs].items():
                assert name.endswith(tokenNameTail), "Wrong tokenname"
                assert amount == 1, "Wrong token amount"
                assert (
                    precNFT == b"" or mintPrecNFT == amount
                ), "OwnNFT should be minted"
        elif isinstance(redeemer, Burn):
            for _, amount in ctx.tx_info.mint[cs].items():
                assert amount == -1, "Own currency needs to be burnt"
    else:
        assert False, "Purpose of mint call must be minting"
