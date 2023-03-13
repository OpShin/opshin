# This is an example of how to determine the structure of the datum files to use with you eopsin custom datums.
# The JSON file is usually required by third party tools like the cardano-cli

# ExampleDatumStructure in Eopsin contract:
"""
@dataclass()
class Listing(PlutusData):
    # Price of the listing in lovelace
    price: int
    # the owner of the listed object
    vendor: Address
    # whoever is allowed to withdraw the listing
    owner: PubKeyHash
"""
# Import the dataclass from the eopsin python file

from examples.smart_contracts.marketplace import (
    Listing,
    Address,
    PubKeyCredential,
    NoStakingCredential,
)

# Create the datum structure in the correct order and print it to use in your transactions for locking unlocking in cardano-cli
datum = Listing(
    5000000,  # This price is in lovelace = 5 ADA
    Address(
        PubKeyCredential(
            bytes.fromhex("f5b84180b5a3cca20052258fe73328c69ff8e0d41709505668101db7")
        ),
        NoStakingCredential(),
    ),
    bytes.fromhex("f5b84180b5a3cca20052258fe73328c69ff8e0d41709505668101db7"),
)

# Export in JSON notation
print(datum.to_json(indent=2))
"""
{
  "constructor": 0,
  "fields": [
    {
      "int": 5000000
    },
    {
      "constructor": 0,
      "fields": [
        {
          "constructor": 0,
          "fields": [
            {
              "bytes": "f5b84180b5a3cca20052258fe73328c69ff8e0d41709505668101db7"
            }
          ]
        },
        {
          "constructor": 1,
          "fields": []
        }
      ]
    },
    {
      "bytes": "f5b84180b5a3cca20052258fe73328c69ff8e0d41709505668101db7"
    }
  ]
}
"""
# Export as CBOR Hex
print(datum.to_cbor(encoding="hex"))
"""d8799f1a004c4b40d8799fd8799f581cf5b84180b5a3cca20052258fe73328c69ff8e0d41709505668101db7ffd87a80ff581cf5b84180b5a3cca20052258fe73328c69ff8e0d41709505668101db7ff"""
