[View code on GitHub](https://github.com/opshin/opshin/examples/extract_datum.py)

This code provides an example of how to determine the structure of the datum files to use with custom datums in the opshin project. The purpose of this code is to create a Listing data structure that can be used in transactions for locking and unlocking in cardano-cli. The Listing data structure is defined as a dataclass in the opshin contract. It has three fields: price, vendor, and owner. The price field is an integer that represents the price of the listing in lovelace. The vendor field is an Address object that contains a PubKeyCredential and a NoStakingCredential. The owner field is a PubKeyHash that represents whoever is allowed to withdraw the listing.

To use this data structure in transactions, the code creates an instance of the Listing class with the correct order of fields. The price is set to 5000000, which is equivalent to 5 ADA in lovelace. The vendor field is an Address object that contains a PubKeyCredential with a specific byte string and a NoStakingCredential. The owner field is set to a specific byte string. The resulting datum is then printed in JSON notation and CBOR Hex encoding.

This code can be used as a reference for creating custom datums in the opshin project. Developers can modify the Listing data structure to fit their specific needs and use it in transactions for locking and unlocking in cardano-cli. The JSON notation and CBOR Hex encoding can be used to export the datum for use in third-party tools. For example, the JSON file can be used by the cardano-cli tool to create transactions. 

Example usage:
```
from examples.smart_contracts.marketplace import (
    Listing,
    Address,
    PubKeyCredential,
    NoStakingCredential,
)

# Create a custom Listing object
my_listing = Listing(
    1000000,  # This price is in lovelace = 1 ADA
    Address(
        PubKeyCredential(
            bytes.fromhex("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
        ),
        NoStakingCredential(),
    ),
    bytes.fromhex("fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"),
)

# Export in JSON notation
print(my_listing.to_json(indent=2))

# Export as CBOR Hex
print(my_listing.to_cbor(encoding="hex"))
```
## Questions: 
 1. What is the purpose of the `Listing` dataclass and what are its attributes?
   - The `Listing` dataclass is used to define the structure of a listing in the opshin contract. It has three attributes: `price` (int), `vendor` (an `Address` object), and `owner` (a `PubKeyHash` object).
   
2. What is the purpose of the `Address`, `PubKeyCredential`, and `NoStakingCredential` classes?
   - These classes are imported from the `examples.smart_contracts.marketplace` module and are used to create an `Address` object, which is an attribute of the `Listing` dataclass. `PubKeyCredential` and `NoStakingCredential` are used to define the `Address` object.
   
3. What is the purpose of the `to_json` and `to_cbor` methods called on the `datum` object?
   - The `to_json` method is used to export the `datum` object in JSON notation, which is required by third party tools like the cardano-cli. The `to_cbor` method is used to export the `datum` object in CBOR Hex format.