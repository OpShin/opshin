from util import *
from contract import VestingParams
from time import time


LIMIT = 6
VESTING_TIME = 30
AMOUNT = 75000000
FEE = 2000000
source = source_vkey.hash().to_primitive()
beneficiary = beneficiary_vkey.hash().to_primitive()
fee_address = fee_address.payment_part.to_primitive()
fee = FEE
deadline = (int(time()) + VESTING_TIME) * 1000
amount = Value(AMOUNT)
datum = VestingParams(source, beneficiary, fee_address, fee, deadline, LIMIT)

builder = TransactionBuilder(context)
builder.add_input_address(source_address)
builder.add_output(TransactionOutput(script_address, amount=amount, datum=datum))
signed_tx = builder.build_and_sign([source_skey], change_address=source_address)

save_transaction(signed_tx, "transactions/tx_deposit.signed")
context.submit_tx(signed_tx.to_cbor())
