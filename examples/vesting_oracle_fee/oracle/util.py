from config import *
from pycardano import Transaction
import json


with open(contract_cbor, "r") as f:
    script_hex = f.read()
contract_script = PlutusV2Script(bytes.fromhex(script_hex))

script_hash = plutus_script_hash(contract_script)
script_address = Address(script_hash, network=network)

oracle_skey = PaymentSigningKey.load(oracle_address_skey)
oracle_vkey = PaymentVerificationKey.from_signing_key(oracle_skey)
oracle_address = Address(oracle_vkey.hash(), network=network)

collateral_skey = PaymentSigningKey.load(collateral_address_skey)
collateral_vkey = PaymentVerificationKey.from_signing_key(collateral_skey)
collateral_address = Address(collateral_vkey.hash(), network=network)


def save_transaction(trans: Transaction, file: str):
    tx = tx_template.copy()
    tx['cborHex'] = trans.to_cbor().hex()
    with open(file, 'w') as tf:
        tf.write(json.dumps(tx, indent=4))
