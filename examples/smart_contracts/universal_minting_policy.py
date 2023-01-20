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
        cs = purpose.policy_id

        if isinstance(redeemer, Mint):
            tokenNameTail = sha256(
                redeemer.ref.out_ref.id + bytes([redeemer.ref.out_ref.idx])
            ).digest()[dn:]
            ref_consumed = False
            for tx_in in ctx.tx_info.inputs:
                if redeemer.ref == tx_in:
                    ref_consumed = True
            assert ref_consumed, "Reference UTxO not consumed"
            mintPrecNFT = ctx.tx_info.mint.get(cs, {b"": 0}).get(precNFT, 0)
            for name, amount in ctx.tx_info.mint.get(cs, {b"": 0}).items():
                assert name.endswith(tokenNameTail), "Wrong tokenname"
                assert amount == 1, "Wrong token amount"
                assert (
                    precNFT == b"" or mintPrecNFT == amount
                ), "OwnNFT should be minted"
        elif isinstance(redeemer, Burn):
            for _, amount in ctx.tx_info.mint.get(cs, {b""}).items():
                assert amount == -1, "Own currency needs to be burnt"
    else:
        assert False, "Purpose of mint call must be minting"
