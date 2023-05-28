from pycardano import *

OGMIOS_URL = "wss://ogmios-preprod-api-public-6763d0.us1.demeter.run:443"
KUPO_URL = "https://kupo-preprod-api-public-6763d0.us1.demeter.run:443"
network = Network.TESTNET
context = OgmiosChainContext(ws_url=OGMIOS_URL, kupo_url=KUPO_URL, network=network)
contract_cbor = "build/contract/script.cbor"
oracle_address = "addr_test1wzddzap6jvpg43dwesg78kyq7c77rz0krjj7g09x727yp8gvrxwd5"
tx_template = {
    "type": "Witnessed Tx BabbageEra",
    "description": "Ledger Cddl Format",
    "cborHex": "",
}
transactions_path = "transactions"
oracle_address_file = "../oracle/build/contract/testnet.addr"
source_address_skey = "wallet/source.skey"
beneficiary_address_skey = "wallet/beneficiary.skey"
fee_address_skey = "wallet/fee.skey"
collateral_address_skey = "wallet/collateral.skey"
