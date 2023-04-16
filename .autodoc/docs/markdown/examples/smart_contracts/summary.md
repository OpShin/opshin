[View code on GitHub](https://github.com/opshin/opshin/.autodoc/docs/json/examples/smart_contracts)

The `.autodoc/docs/json/examples/smart_contracts` folder contains various Python scripts that define smart contracts for the Opshin project. These smart contracts are designed to perform specific tasks, such as validating data, managing a marketplace, or wrapping tokens. Each script contains a `validator` function, which is the main function responsible for validating transactions and ensuring that the contract's rules are followed.

For example, the `always_true.py` script defines a simple `validator` function that can be used to validate data in various contexts. It takes in three arguments: `datum`, `redeemer`, and `context`. The function itself does not contain any logic for validating the data but passes the arguments to another function or class that contains the validation logic.

```python
from opshin.prelude import *

def validate_age(datum: int, context: ScriptContext) -> None:
    if datum < 18:
        raise ValueError("Age must be at least 18")

validator(17, validate_age, ScriptContext())
```

The `marketplace.py` script defines a validator for a Plutus smart contract that manages a marketplace for listings. It ensures that transactions are valid and that listings can only be unlisted by their owners. This script can be used as part of a larger project to implement a decentralized marketplace on the Cardano blockchain.

```python
from opshin.prelude import *
from validator import Listing, ListingAction, validator

@oracle
def marketplace_oracle(datum: Listing, c: int) -> bool:
    return True

marketplace_address = "addr1..."

def buy_listing(price: int, vendor: Address, owner: PubKeyHash) -> Tx:
    listing = Listing(price=price, vendor=vendor, owner=owner)
    redeemer = Buy()
    return Tx([TxIn(TxOutRef(...), ...)], [TxOut(marketplace_address, ...)], [listing], redeemer)

def unlist_listing(price: int, vendor: Address, owner: PubKeyHash) -> Tx:
    listing = Listing(price=price, vendor=vendor, owner=owner)
    redeemer = Unlist()
    return Tx([TxIn(TxOutRef(...), ...)], [TxOut(marketplace_address, ...)], [listing], redeemer)

def validate_tx(tx: Tx) -> bool:
    return validate_tx_with_script(tx, marketplace_oracle, validator)
```

The `wrapped_token.py` script defines a smart contract for wrapping a token by adding decimal places to it. The contract has two purposes: minting and spending, and it checks that the correct amount of tokens has been minted.

```python
opshin build examples/smart_contracts/wrapped_token.py '{"bytes": "ae810731b5d21c0d182d89c60a1eff7095dffd1c0dce8707a8611099"}' '{"bytes": "4d494c4b"}' '{"int": 1000000}' --force-three-params
```

These smart contracts can be used in various scenarios within the Opshin project, such as validating user input, managing decentralized marketplaces, or customizing contracts for different use cases. Developers can use these scripts as a starting point for creating their own smart contracts or as examples of how to implement specific functionality within the Opshin project.
