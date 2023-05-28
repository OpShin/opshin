from oracle.config import *
from vesting.config import *

oracle_skey = PaymentSigningKey.load('oracle/' + oracle_address_skey)
oracle_vkey = PaymentVerificationKey.from_signing_key(oracle_skey)
oracle_address = Address(oracle_vkey.hash(), network=network)

oracle_collateral_skey = PaymentSigningKey.load('oracle/' + collateral_address_skey)
oracle_collateral_vkey = PaymentVerificationKey.from_signing_key(oracle_collateral_skey)
oracle_collateral_address = Address(oracle_collateral_vkey.hash(), network=network)

source_skey = PaymentSigningKey.load('vesting/' + source_address_skey)
source_vkey = PaymentVerificationKey.from_signing_key(source_skey)
source_address = Address(source_vkey.hash(), network=network)

beneficiary_skey = PaymentSigningKey.load('vesting/' + beneficiary_address_skey)
beneficiary_vkey = PaymentVerificationKey.from_signing_key(beneficiary_skey)
beneficiary_address = Address(beneficiary_vkey.hash(), network=network)

vesting_collateral_skey = PaymentSigningKey.load('vesting/' + collateral_address_skey)
vesting_collateral_vkey = PaymentVerificationKey.from_signing_key(vesting_collateral_skey)
vesting_collateral_address = Address(vesting_collateral_vkey.hash(), network=network)

builder = TransactionBuilder(context)
builder.add_input_address(source_address)
builder.add_output(TransactionOutput.from_primitive([oracle_collateral_address.encode(), 5000000]))
builder.add_output(TransactionOutput.from_primitive([vesting_collateral_address.encode(), 5000000]))
builder.add_output(TransactionOutput.from_primitive([oracle_address.encode(), 100000000]))
builder.add_output(TransactionOutput.from_primitive([beneficiary_address.encode(), 100000000]))
signed_tx = builder.build_and_sign([source_skey], change_address=source_address)
context.submit_tx(signed_tx.to_cbor())
