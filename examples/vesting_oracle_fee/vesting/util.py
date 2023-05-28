from config import *
from pycardano import Transaction
import json


with open(contract_cbor, "r") as f:
    script_hex = f.read()
contract_script = PlutusV2Script(bytes.fromhex(script_hex))

with open(oracle_address_file, "r") as f:
    oracle_address = f.read().strip()

script_hash = plutus_script_hash(contract_script)
script_address = Address(script_hash, network=network)

source_skey = PaymentSigningKey.load(source_address_skey)
source_vkey = PaymentVerificationKey.from_signing_key(source_skey)
source_address = Address(source_vkey.hash(), network=network)

beneficiary_skey = PaymentSigningKey.load(beneficiary_address_skey)
beneficiary_vkey = PaymentVerificationKey.from_signing_key(beneficiary_skey)
beneficiary_address = Address(beneficiary_vkey.hash(), network=network)

fee_skey = PaymentSigningKey.load(fee_address_skey)
fee_vkey = PaymentVerificationKey.from_signing_key(fee_skey)
fee_address = Address(fee_vkey.hash(), network=network)

collateral_skey = PaymentSigningKey.load(collateral_address_skey)
collateral_vkey = PaymentVerificationKey.from_signing_key(collateral_skey)
collateral_address = Address(collateral_vkey.hash(), network=network)


def save_transaction(trans: Transaction, file: str):
    tx = tx_template.copy()
    tx["cborHex"] = trans.to_cbor().hex()
    with open(file, "w") as tf:
        tf.write(json.dumps(tx, indent=4))
