from util import *
from contract import VestingParams, ClaimRedeemer, PublishParams
import cbor2


oracle_utxos = context.utxos(oracle_address)
oracle_utxo = ""
for item in oracle_utxos:
    if item.output.datum and not item.output.script:
        oracle_utxo = item
        oracle_datum = cbor2.loads(item.output.datum.cbor)
        oracle_datum_obj = PublishParams(
            oracle_datum.value[0], oracle_datum.value[1], oracle_datum.value[2]
        )
if not oracle_utxo:
    print("oracle Datum UTxO not found!")
    exit(1)

script_utxos = context.utxos(str(script_address))
sc_utxo = ""
claimable_utxos = []

for item in script_utxos:
    if item.output.script:
        sc_utxo = item
    elif item.output.datum:
        datum = cbor2.loads(item.output.datum.cbor)
        datum_obj = VestingParams(
            datum.value[0],
            datum.value[1],
            datum.value[2],
            datum.value[3],
            datum.value[4],
            datum.value[5],
        )
        if str(datum_obj.beneficiary.hex()) == str(beneficiary_vkey.hash()):
            beneficiary = Address(
                VerificationKeyHash.from_primitive(datum_obj.beneficiary),
                network=network,
            )
            fee_address = Address(
                VerificationKeyHash.from_primitive(datum_obj.fee_address),
                network=network,
            )
            """
            TODO: also check if the deadline has passed and if the oracle datum info is greater than the datum limit
            """
            claimable_utxos.append(
                {"fee_address": str(fee_address), "fee": datum_obj.fee, "utxo": item}
            )

if not sc_utxo:
    print("smart contract UTxO not found!")
    exit(1)

if not len(claimable_utxos):
    print("no utxo to claim!")
    exit(1)

collateral_utxo = context.utxos(str(collateral_address))[0]

builder = TransactionBuilder(context)
builder.reference_inputs.add(sc_utxo)
builder.reference_inputs.add(oracle_utxo)
for utxo_to_spend in claimable_utxos:
    builder.add_script_input(utxo_to_spend["utxo"], redeemer=Redeemer(ClaimRedeemer()))
    builder.add_output(
        TransactionOutput.from_primitive(
            [utxo_to_spend["fee_address"], utxo_to_spend["fee"]]
        )
    )

builder.collaterals.append(collateral_utxo)
builder.required_signers = [beneficiary_vkey.hash(), collateral_vkey.hash()]
builder.validity_start = context.last_block_slot
builder.ttl = builder.validity_start + 3600
signed_tx = builder.build_and_sign(
    [beneficiary_skey, collateral_skey], change_address=beneficiary_address
)

save_transaction(signed_tx, "transactions/tx_claim.signed")
context.submit_tx(signed_tx.to_cbor())
