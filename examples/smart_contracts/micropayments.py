from dataclasses import astuple
from opshin.ledger.api_v3 import *
from opshin.std.builtins import *
from opshin.std.integrity import check_integrity
from opshin.prelude import *

"""
A micropayment channel between Alice and Bob that lets users exchange funds simply by exchanging signed numbers (off-chain).
The actual value transfer can happen at any time and be initiated by any party using the signed values.
This is just an example of a complex contract and should not be used in production without further examination.
"""


@dataclass()
class PaymentChannel(PlutusData):
    CONSTR_ID = 0
    balance_alice: int
    pubkeyhash_alice: bytes
    balance_bob: int
    pubkeyhash_bob: bytes
    nonce: int


@dataclass()
class MicropaymentAlice(PlutusData):
    """Alice pays Bob amount x"""

    CONSTR_ID = 0  # Needed to distinguish different datums
    amount: int
    nonce: int
    # The signature of str(amount) + str(nonce), signed with alice's secret key
    sig: bytes


@dataclass()
class MicropaymentBob(PlutusData):
    """Bob pays Alice amount x"""

    CONSTR_ID = 1  # Needed to distinguish different datums
    amount: int
    nonce: int
    # The signature of str(amount) + str(nonce), signed with bob's secret key
    sig: bytes


Micropayment = Union[MicropaymentAlice, MicropaymentBob]


@dataclass()
class Micropayments(PlutusData):
    """A sequence of micropayments to be applied to the channel"""

    CONSTR_ID = 0
    payments: List[Micropayment]


@dataclass()
class TearDown(PlutusData):
    """The microchannel is torn down and all participants receive their amounts. Can be initiated by any party"""

    CONSTR_ID = 1


# The setup is implicit! Just send a UTxO to the channel address with the correct datum & amounts
ChannelAction = Union[Micropayments, TearDown]


def validate_channel(
    datum: PaymentChannel, redeemer: ChannelAction, context: ScriptContext
) -> None:
    # Ensure that the redeemer is well formed
    check_integrity(redeemer)
    purpose = context.purpose
    assert isinstance(purpose, Spending), "Can only spend from the contract"
    check_integrity(datum)
    (
        balance_alice_datum,
        pubkeyhash_alice,
        balance_bob_datum,
        pubkeyhash_bob,
        nonce_datum,
    ) = astuple(datum)

    if isinstance(redeemer, TearDown):
        # Ensure that either party signed this request
        assert (
            pubkeyhash_alice in context.transaction.signatories
            or pubkeyhash_bob in context.transaction.signatories
        ), f"Neither Alice nor Bob signed the transaction, signatory list: {context.transaction.signatories}"
        # Ensure that all participants receive their amounts
        amount_alice = 0
        amount_bob = 0
        for o in context.transaction.outputs:
            # Note: in a real world scenario, you will want to make sure the stake key hash matches too!
            pkh = o.address.payment_credential.credential_hash
            if pkh == pubkeyhash_alice:
                amount_alice += o.value.get(b"", {b"": 0}).get(b"", 0)
            elif pkh == pubkeyhash_bob:
                amount_bob += o.value.get(b"", {b"": 0}).get(b"", 0)
        assert (
            amount_alice >= balance_alice_datum
        ), f"Alice does not receive enough, expecting {balance_alice_datum}, receiving {amount_alice}"
        assert (
            amount_bob >= balance_bob_datum
        ), f"Bob does not receive enough, expecting {balance_bob_datum}, receiving {amount_bob}"
        # That's it!
    elif isinstance(redeemer, Micropayments):
        # Squash apply the micropayments
        balance_alice = balance_alice_datum
        balance_bob = balance_bob_datum
        nonce = nonce_datum
        # Ensure that the payments are all valid and accumulate state
        for payment in redeemer.payments:
            assert (
                payment.nonce > nonce
            ), f"Invalid nonce, replay attack detected ({payment.nonce} <= {nonce})"
            assert (
                payment.amount > 0
            ), f"Invalid amount transfer {payment.amount}, must be positive"
            nonce = payment.nonce
            if isinstance(payment, MicropaymentAlice):
                assert verify_ed25519_signature(
                    pubkeyhash_alice,
                    (str(payment.amount) + str(nonce)).encode(),
                    payment.sig,
                ), "Invalid signature of Alice for micropayment"
                balance_alice -= payment.amount
                balance_bob += payment.amount
            elif isinstance(payment, MicropaymentBob):
                assert verify_ed25519_signature(
                    pubkeyhash_bob,
                    (str(payment.amount) + str(nonce)).encode(),
                    payment.sig,
                ), "Invalid signature of Bob for micropayment"
                balance_alice += payment.amount
                balance_bob -= payment.amount
            else:
                assert False, "Invalid type of micropayment!"

        own_tx_out_ref = purpose.tx_out_ref
        # this stunt is just to find the output that goes to the same address as the input we are validating to be spent
        own_tx_out = [
            i for i in context.transaction.inputs if i.out_ref == own_tx_out_ref
        ][0].resolved
        own_address = own_tx_out.address
        cont_tx_out = [
            o for o in context.transaction.outputs if o.address == own_address
        ][0]
        # The value = locked tokens must not change
        for pid, tn_dict in own_tx_out.value.items():
            for tokenname, amount in tn_dict.items():
                assert (
                    amount <= cont_tx_out.value[pid][tokenname]
                ), f"Value of token in payment channel has decreased from {amount} to {cont_tx_out.value[pid][tokenname]}"
        cont_datum = cont_tx_out.datum
        assert isinstance(
            cont_datum, SomeOutputDatum
        ), f"Must inline attached datum, got {cont_datum}"
        # We cast the datum to payment channel (it is stored without structure in the ledger)
        cont_datum_content: PaymentChannel = cont_datum.datum
        # Technically not needed because we compare for exact equality below, but good practice
        check_integrity(cont_datum_content)
        # Ensure that the state is correctly updated
        assert cont_datum_content == PaymentChannel(
            balance_alice,
            pubkeyhash_alice,
            balance_bob,
            pubkeyhash_bob,
            nonce,
        )
    else:
        # Other redeemers are not allowed!
        assert False, "Wrong redeemer passed!"


@dataclass()
class Contract:
    def spend_with_datum(
        self, datum: PaymentChannel, redeemer: ChannelAction, context: ScriptContext
    ) -> None:
        validate_channel(datum, redeemer, context)
