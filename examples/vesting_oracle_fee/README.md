# Vesting with fee and Oracle Datum condition

This example has 2 Opshin smart contracts:

## Oracle
This smart contract is a simple Oracle publishing an integer in a Datum on-chain. 
Other smart contracts can use this integer and take decisions depending on its value.

## Vesting
This smart contract is a more complex vesting smart contract. In order to unlock locked funds, it checks if:
- the transaction is signed by its beneficiary (a key defined in the Datum when locking the funds)
- the vesting period passed (also declared in the Datum when locking the funds)
- a fee is paid to an address (the fee address and fee amount are also declared in the Datum when locking the funds)
- the `limit` declared in the same Datum is lower than the integer published by the Oracle in its own Datum

This is only presented as an example, anyone can publish an UTxO at the Oracle address with a different integer 
which may allow unlocking the funds. There is no check implemented regarding who published the Oracle Datum.

In order to test this example, the following steps can be performed:

Clone the repository:
```shell
https://github.com/OpShin/opshin.git
```

Create the virtual environment (for example in the `examples/vesting_oracle_fee` folder):
```shell
cd opshin/examples/vesting_oracle_fee
virtualenv -p python3 venv
```

Activate the virtual environment:
```shell
. venv/bin/activate
```

Install the required modules:
```shell
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Create the payment addresses.<br>
In the `oracle/wallet` folder:
```shell
. payment-addreses.sh
```
In the `vesting/wallet` folder:
```shell
. payment-addreses.sh
```

Fund the `source address` from https://docs.cardano.org/cardano-testnet/tools/faucet/ on the `preprod` network.
Distribute some funds to the collateral addresses, to the oracle address and to the vesting beneficiary address.<br>
In the root folder of the example (where this README.md file is):
```shell
python3 distribute_funds.py
```

Build and deploy the smart contracts.<br>
In the `oracle` folder:
```shell
opshin build spending contract.py
echo $(cat build/contract/testnet.addr)
python3 deploy.py
```

In the `vesting` folder:
```shell
opshin build spending contract.py
echo $(cat build/contract/testnet.addr)
python3 deploy.py
```
You can see the addresses and transaction on the blockchain explorer: https://preprod.cardanoscan.io/

Deposit some ADA for the beneficiary on the Vesting smart contract address.  In the example, in order to claim 
the deposit, the beneficiary will have to pay a fee to a fee address, and he will only be able to claim if the 
Oracle will publish a Datum with useful information which is higher than the `VestingParams.limit` in the deposit. 
The `VestingParams` class it the Datum format declared in `contract.py`. 
In the example, the vesting time is set to 30 seconds, the `limit` is set to 6 
and the `fee` is 2 ADA.<br>
In the `vesting` folder:
```shell
python3 deposit.py
```

Publish a Datum with useful information on the Oracle smart contract address. 
The useful information in this example is the integer 7. This will allow the beneficiary to claim the deposit, because 
the smart contract checks if the integer published by the Oracle is greater than the `limit` in the deposit's datum.<br>
In the `oracle` folder:
```shell
python3 publish.py
```

Claim the deposit.<br>
In the `vesting` folder:
```shell
python3 claim.py
```

Test setting a `limit` higher than 7 and a longer vesting period by editing the `deposit.py` in the `vesting` folder, 
then run it again:
```shell
python3 deposit.py
```
Claiming before the vesting period expires will throw the error `'TX submitted too early!'`, and after the vesting 
period, the error will be `'Claim condition not met!'`. If the beneficiary signature is missing from the claim 
transaction, the error will be `{'missingRequiredSignatures': ['<beneficiary_public_key_hash>']}`.
If the fee is not paid, the error will be `'Fee address not found in outputs!'`, 
and if the fee amount is too low, the error will be `'Fee too small!'`.

The deposit can be refunded anytime by running the `refund.py` script in the `vesting` folder:
```shell
python3 refund.py
```

The Oracle Datum UTxO can also be refunded when it is no longer required by running the `refund.py` script 
in the `oracle` folder:
```shell
python3 refund.py
```

At the end, the smart contract UTxOs can also be spent ("un-deployed") by running the `undeploy.py` scripts in the 
`oracle`, respectively `vesting` folder:
```shell
python3 undeploy.py
```
