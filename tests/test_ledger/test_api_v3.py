from cbor2 import CBORTag
from parameterized import parameterized
from pycardano import RawPlutusData

from opshin.ledger.api_v3 import *


@parameterized.expand(
    [
        # Standard script invocation for spending
        (
            "d8799fd8799f81d8799fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd8799fd87a9f581c4154af4452c57951a0d4e9bfd36ef809c6f49ed8a66967e51cbdc314ffd87a80ffa140a1401a002dc6c0d87b9fd87980ffd87a80ffff8081d8799fd8799fd8799f581c61299458bd6d3011669ac533b520ab07b94d7428903f61714babb582ffd87a80ffa140a1401a002b112bd87980d87a80ff1a0002b595a080a0d8799fd8799fd87a9f1b0000019667dbfac0ffd87a80ffd8799fd87a9f1b0000019667ead388ffd87980ffff80a1d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffff00a05820ffa18bad2d7b861a44b07af9df6c42b60414bf0e5279134293001aea66ead701a080d87a80d87a80ff00d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd87980ffffff"
        ),
        # additionally contains a vote
        (
            "d8799fd8799f81d8799fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd8799fd87a9f581c4154af4452c57951a0d4e9bfd36ef809c6f49ed8a66967e51cbdc314ffd87a80ffa140a1401a002dc6c0d87b9fd87980ffd87a80ffff8081d8799fd8799fd8799f581c61299458bd6d3011669ac533b520ab07b94d7428903f61714babb582ffd87a80ffa140a1401a002b041bd87980d87a80ff1a0002c2a5a080a0d8799fd8799fd87a9f1b0000019667f2af40ffd87a80ffd8799fd87a9f1b0000019668021890ffd87980ffff80a1d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffff00a05820bdb6e7f3d88a9e5b2c88fa78fee817c1f73c8a2edc48ede2ae4962a32de7b323a1d87a9fd8799f581c61299458bd6d3011669ac533b520ab07b94d7428903f61714babb582ffffa1d8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd87a8080d87a80d87a80ff00d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd87980ffffff"
        ),
        # additionally contains a treasury donation and statement
        (
            "d8799fd8799f81d8799fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd8799fd87a9f581c4154af4452c57951a0d4e9bfd36ef809c6f49ed8a66967e51cbdc314ffd87a80ffa140a1401a002dc6c0d87b9fd87980ffd87a80ffff8081d8799fd8799fd8799f581c61299458bd6d3011669ac533b520ab07b94d7428903f61714babb582ffd87a80ffa140a1401a002b020bd87980d87a80ff1a0002c4b5a080a0d8799fd8799fd87a9f1b0000019667fd4248ffd87a80ffd8799fd87a9f1b00000196680cab98ffd87980ffff80a1d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffff00a05820f77e175d767ce3b5b56e16fbfa7a8d97e67980ec4bd8784134e607a0584333bea1d87a9fd8799f581c61299458bd6d3011669ac533b520ab07b94d7428903f61714babb582ffffa1d8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd87a8080d8799f1a00bc4ff2ffd8799f1a05f76804ffff00d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd87980ffffff"
        ),
    ]
)
def test_script_context_repr_correct(p):
    # Make sure that this parses correctly and does not throw an error
    # Note that this was extracted from a PlutusV3 invocation
    # in increasing complexity
    ScriptContext.from_cbor(p)


def test_script_context_mapping():
    context = "d8799fd8799f81d8799fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd8799fd87a9f581c4154af4452c57951a0d4e9bfd36ef809c6f49ed8a66967e51cbdc314ffd87a80ffa140a1401a002dc6c0d87b9fd87980ffd87a80ffff8081d8799fd8799fd8799f581c61299458bd6d3011669ac533b520ab07b94d7428903f61714babb582ffd87a80ffa140a1401a002b020bd87980d87a80ff1a0002c4b5a080a0d8799fd8799fd87a9f1b0000019667fd4248ffd87a80ffd8799fd87a9f1b00000196680cab98ffd87980ffff80a1d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffff00a05820f77e175d767ce3b5b56e16fbfa7a8d97e67980ec4bd8784134e607a0584333bea1d87a9fd8799f581c61299458bd6d3011669ac533b520ab07b94d7428903f61714babb582ffffa1d8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd87a8080d8799f1a00bc4ff2ffd8799f1a05f76804ffff00d87a9fd8799f5820ec7874002d9b55a81e64eefcb3b41f8897eb36ad61c3392661f8a7c5a39879a500ffd8799fd87980ffffff"
    sc = ScriptContext.from_cbor(context)
    assert sc == ScriptContext(
        transaction=TxInfo(
            inputs=[
                TxInInfo(
                    out_ref=TxOutRef(
                        id=b"\xecxt\x00-\x9bU\xa8\x1ed\xee\xfc\xb3\xb4\x1f\x88\x97\xeb6\xada\xc39&a\xf8\xa7\xc5\xa3\x98y\xa5",
                        idx=0,
                    ),
                    resolved=TxOut(
                        address=Address(
                            payment_credential=ScriptCredential(
                                credential_hash=b"AT\xafDR\xc5yQ\xa0\xd4\xe9\xbf\xd3n\xf8\t\xc6\xf4\x9e\xd8\xa6ig\xe5\x1c\xbd\xc3\x14"
                            ),
                            staking_credential=NoStakingCredential(),
                        ),
                        value={b"": {b"": 3000000}},
                        datum=SomeOutputDatum(
                            datum=RawPlutusData(data=CBORTag(121, []))
                        ),
                        reference_script=NoScriptHash(),
                    ),
                )
            ],
            reference_inputs=[],
            outputs=[
                TxOut(
                    address=Address(
                        payment_credential=PubKeyCredential(
                            credential_hash=b"a)\x94X\xbdm0\x11f\x9a\xc53\xb5 \xab\x07\xb9Mt(\x90?aqK\xab\xb5\x82"
                        ),
                        staking_credential=NoStakingCredential(),
                    ),
                    value={b"": {b"": 2818571}},
                    datum=NoOutputDatum(),
                    reference_script=NoScriptHash(),
                )
            ],
            fee=181429,
            mint={},
            certificates=[],
            withdrawals={},
            validity_range=POSIXTimeRange(
                lower_bound=LowerBoundPOSIXTime(
                    limit=FinitePOSIXTime(time=1745501373000), closed=TrueData()
                ),
                upper_bound=UpperBoundPOSIXTime(
                    limit=FinitePOSIXTime(time=1745502383000), closed=FalseData()
                ),
            ),
            signatories=[],
            redeemers={
                Spending(
                    tx_out_ref=TxOutRef(
                        id=b"\xecxt\x00-\x9bU\xa8\x1ed\xee\xfc\xb3\xb4\x1f\x88\x97\xeb6\xada\xc39&a\xf8\xa7\xc5\xa3\x98y\xa5",
                        idx=0,
                    )
                ): 0
            },
            datums={},
            id=b"\xf7~\x17]v|\xe3\xb5\xb5n\x16\xfb\xfaz\x8d\x97\xe6y\x80\xecK\xd8xA4\xe6\x07\xa0XC3\xbe",
            votes={
                DelegateRepresentative(
                    credential=PubKeyCredential(
                        credential_hash=b"a)\x94X\xbdm0\x11f\x9a\xc53\xb5 \xab\x07\xb9Mt(\x90?aqK\xab\xb5\x82"
                    )
                ): {
                    GovernanceActionId(
                        transaction=b"\xecxt\x00-\x9bU\xa8\x1ed\xee\xfc\xb3\xb4\x1f\x88\x97\xeb6\xada\xc39&a\xf8\xa7\xc5\xa3\x98y\xa5",
                        proposal_procedure=0,
                    ): VoteYes()
                }
            },
            proposal_procedures=[],
            current_treasury_amount=BoxedInt(value=12341234),
            treasury_donation=BoxedInt(value=100100100),
        ),
        redeemer=0,
        purpose=Spending(
            tx_out_ref=TxOutRef(
                id=b"\xecxt\x00-\x9bU\xa8\x1ed\xee\xfc\xb3\xb4\x1f\x88\x97\xeb6\xada\xc39&a\xf8\xa7\xc5\xa3\x98y\xa5",
                idx=0,
            )
        ),
    )
