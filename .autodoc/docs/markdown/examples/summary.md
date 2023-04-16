[View code on GitHub](https://github.com/opshin/opshin/.autodoc/docs/json/examples)

The `.autodoc/docs/json/examples` folder contains various Python scripts that demonstrate different functionalities and use cases within the Opshin project. These scripts define data classes, validator functions, and smart contracts that can be used in different parts of the project, such as validating user input, managing decentralized marketplaces, or customizing contracts for different use cases.

For instance, the `complex_datum.py` script defines data classes and a union type for representing batch orders in a decentralized exchange on the Cardano blockchain. The `validator` function in this script can be used to validate batch orders and ensure they were created by the correct sender. Example usage of this script is as follows:

```python
# Create a deposit order step
deposit = Deposit(CONSTR_ID=0, minimum_lp=100)

# Create a batch order with the deposit order step
batch_order = BatchOrder(sender=sender_address, receiver=receiver_address, receiver_datum_hash=None, order_step=deposit, batcher_fee=10, output_ada=1000, pool_nft_tokenname="POOL", script_version=b"v1")

# Validate the batch order
validator_result = validator(batch_order)
```

Another example is the `extract_datum.py` script, which demonstrates how to create a custom datum for use in transactions with cardano-cli. Developers can modify the provided `Listing` data structure to fit their specific needs and use it in transactions for locking and unlocking in cardano-cli. Example usage:

```python
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

The `smart_contracts` subfolder contains various Python scripts that define smart contracts for the Opshin project. These smart contracts are designed to perform specific tasks, such as validating data, managing a marketplace, or wrapping tokens. Each script contains a `validator` function, which is the main function responsible for validating transactions and ensuring that the contract's rules are followed.

In summary, the `.autodoc/docs/json/examples` folder provides a collection of Python scripts that showcase different functionalities and use cases within the Opshin project. Developers can use these scripts as a starting point for creating their own smart contracts or as examples of how to implement specific functionality within the Opshin project.
