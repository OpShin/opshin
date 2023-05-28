from util import *
from contract import RefundRedeemer
import json


script_utxos = context.utxos(str(script_address))
sc_utxo = ""
utxo_to_spend = ""
for item in script_utxos:
    if item.output.script:
        sc_utxo = item
    elif item.output.datum:
        utxo_to_spend = item

if not sc_utxo:
    print("smart contract UTxO not found!")
    exit(1)

if not utxo_to_spend:
    print("no utxo to refund!")
    exit(1)

collateral_utxo = context.utxos(str(collateral_address))[0]
redeemer = Redeemer(RefundRedeemer())

builder = TransactionBuilder(context)
builder.reference_inputs.add(sc_utxo)
builder.add_script_input(utxo_to_spend, redeemer=redeemer)
# builder.add_script_input(utxo_to_spend, redeemer=redeemer, script=contract_script)
builder.collaterals.append(collateral_utxo)
builder.required_signers = [payment1_vkey.hash(), collateral_vkey.hash()]
builder.validity_start = context.last_block_slot
builder.ttl = builder.validity_start + 3600
signed_tx = builder.build_and_sign(
    [payment1_skey, collateral_skey], change_address=payment1_address
)

save_transaction(signed_tx, "transactions/tx_refund.signed")
context.submit_tx(signed_tx.to_cbor())
