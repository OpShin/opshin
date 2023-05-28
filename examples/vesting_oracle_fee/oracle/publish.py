from util import *
from contract import PublishParams
from time import time


INFO = 7
AMOUNT = 12500000
VALIDITY_TIME = 300
owner = oracle_vkey.hash().to_primitive()
deadline = int(time() + VALIDITY_TIME) * 1000
amount = Value(AMOUNT)
datum = PublishParams(owner, deadline, INFO)

builder = TransactionBuilder(context)
builder.add_input_address(oracle_address)
builder.add_output(TransactionOutput(script_address, amount=amount, datum=datum))
signed_tx = builder.build_and_sign([oracle_skey], change_address=oracle_address)

save_transaction(signed_tx, 'transactions/tx_deposit.signed')
context.submit_tx(signed_tx.to_cbor())
