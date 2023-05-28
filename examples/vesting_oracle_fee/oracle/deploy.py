from util import *
from contract import PublishParams
from time import time


owner = oracle_vkey.hash().to_primitive()
deadline = int(time()) * 1000
amount = Value(40000000)

datum = PublishParams(
    owner=owner,
    deadline=deadline,
    info=0
)

builder = TransactionBuilder(context)
builder.add_input_address(oracle_address)
builder.add_output(TransactionOutput(script_address, amount=amount, datum=datum, script=contract_script))
signed_tx = builder.build_and_sign([oracle_skey], change_address=oracle_address)

save_transaction(signed_tx, 'transactions/tx_deploy.signed')
context.submit_tx(signed_tx.to_cbor())
