from util import *
from contract import VestingParams
from time import time


deployer = source_vkey.hash().to_primitive()
fee_address = source_address.payment_part.to_primitive()

limit = 0
fee = 2000000
deadline = int(time()) * 1000
amount = Value(50000000)

datum = VestingParams(
    source=deployer,
    beneficiary=deployer,
    fee_address=fee_address,
    fee=fee,
    deadline=deadline,
    limit=limit
)

builder = TransactionBuilder(context)
builder.add_input_address(source_address)
builder.add_output(TransactionOutput(script_address, amount=amount, datum=datum, script=contract_script))
signed_tx = builder.build_and_sign([source_skey], change_address=source_address)

save_transaction(signed_tx, 'transactions/tx_deploy.signed')
context.submit_tx(signed_tx.to_cbor())
