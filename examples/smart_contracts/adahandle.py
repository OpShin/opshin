from opshin.prelude import *

ADAHANDLE_POLICYID = bytes.fromhex(
    "f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a"
)


def validator(d, r, ctx: ScriptContext):

    adahandle_present = False

    for input in ctx.tx_info.inputs:
        for policy_id, m in input.resolved.value.items():
            if policy_id == ADAHANDLE_POLICYID and b"$opshin" in m.keys():
                adahandle_present = True

    assert adahandle_present, "Required ada handle missing!"
