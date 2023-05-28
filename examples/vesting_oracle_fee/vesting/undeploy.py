from util import *
from contract import RefundRedeemer


script_utxos = context.utxos(str(script_address))
sc_utxo = ''
utxo_to_spend = ''
for item in script_utxos:
    if item.output.script:
        sc_utxo = item
        utxo_to_spend = item

if not sc_utxo or not utxo_to_spend:
    print('no script input or not utxo to spend!')
    exit(1)

collateral_utxo = context.utxos(str(collateral_address))[0]
redeemer = Redeemer(RefundRedeemer())

builder = TransactionBuilder(context)
builder.add_script_input(sc_utxo, redeemer=redeemer)
builder.collaterals.append(collateral_utxo)
builder.validity_start = context.last_block_slot
builder.ttl = builder.validity_start + 3600
builder.required_signers = [source_vkey.hash(), collateral_vkey.hash()]
signed_tx = builder.build_and_sign([source_skey, collateral_skey], change_address=source_address)

save_transaction(signed_tx, 'transactions/tx_undeploy.signed')
context.submit_tx(signed_tx.to_cbor())
