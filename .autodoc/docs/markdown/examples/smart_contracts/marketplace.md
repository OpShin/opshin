[View code on GitHub](https://github.com/opshin/opshin/examples/smart_contracts/marketplace.py)

This code defines a validator script for a Plutus smart contract that manages a marketplace for listings. The script defines three data classes: `Listing`, `Buy`, and `Unlist`. `Listing` represents a listing on the marketplace and contains information about the price, vendor, and owner. `Buy` and `Unlist` are used as redeemer values to indicate whether a transaction is intended to buy a listing or unlist a listing. The `ListingAction` type is defined as a union of `Buy` and `Unlist`.

The script also defines three helper functions: `check_paid`, `check_single_utxo_spent`, and `check_owner_signed`. `check_paid` checks that the correct amount of lovelace has been paid to the vendor for a listing. `check_single_utxo_spent` checks that only one UTxO is unlocked from the contract address to prevent double spending. `check_owner_signed` checks that the owner of a listing has signed a transaction to unlist the listing.

The `validator` function is the main function of the script and takes three arguments: `datum`, `redeemer`, and `context`. `datum` is an instance of `Listing` that represents the current state of the contract. `redeemer` is an instance of `ListingAction` that indicates the purpose of the transaction. `context` is an instance of `ScriptContext` that contains information about the current transaction.

The `validator` function first checks the purpose of the transaction to ensure that it is a spending transaction. It then resolves the spent UTxO and checks that only one UTxO is spent. If the redeemer is `Buy`, it checks that the correct amount of lovelace has been paid to the vendor. If the redeemer is `Unlist`, it checks that the owner of the listing has signed the transaction.

Overall, this script provides a basic validator for a Plutus smart contract that manages a marketplace for listings. It ensures that transactions are valid and that listings can only be unlisted by their owners. This script can be used as part of a larger project to implement a decentralized marketplace on the Cardano blockchain. An example usage of this script might look like:

```
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
## Questions: 
 1. What is the purpose of the `Listing` and `ListingAction` classes?
- The `Listing` class represents a listing with a price, vendor, and owner, while the `ListingAction` class is a union of `Buy` and `Unlist` classes that represent actions that can be taken on a listing.

2. What do the `check_paid` and `check_single_utxo_spent` functions do?
- `check_paid` checks that the correct amount of lovelace has been paid to the vendor for a listing, while `check_single_utxo_spent` ensures that only one UTxO is unlocked from the contract address to prevent double spending.

3. What is the purpose of the `validator` function?
- The `validator` function takes in a `datum` (a `Listing` object), a `redeemer` (a `ListingAction` object), and a `context` (a `ScriptContext` object) and performs various checks to ensure that the transaction is valid, depending on the type of `redeemer` passed in.