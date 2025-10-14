from opshin.ledger.interval import *
from opshin.prelude import *


@dataclass()
class VestingParams(PlutusData):
    beneficiary: bytes
    deadline: POSIXTime


def signed_by_beneficiary(params: VestingParams, context: ScriptContext) -> bool:
    return params.beneficiary in context.transaction.signatories


def is_after(deadline: POSIXTime, valid_range: POSIXTimeRange) -> bool:
    # To ensure that the `valid_range` occurs after the `deadline`,
    # we construct an interval from `deadline` to infinity
    # then check whether that interval contains the `valid_range` interval.
    from_interval: POSIXTimeRange = make_from(deadline)
    return contains(from_interval, valid_range)


def deadline_reached(params: VestingParams, context: ScriptContext) -> bool:
    # The current transaction can only execute in `valid_range`,
    # so the current execution time is always within `valid_range`.
    # Therefore, to make all possible execution times occur after the deadline,
    # we need to make sure the whole `valid_range` interval occurs after the `deadline`.
    return is_after(params.deadline, context.transaction.validity_range)


def validator(context: ScriptContext) -> None:
    purpose = context.purpose
    assert isinstance(purpose, Spending)
    own_utxo = own_spent_utxo(context.transaction.inputs, purpose)
    datum: VestingParams = resolve_datum_unsafe(own_utxo, context.transaction)
    assert signed_by_beneficiary(datum, context), "beneficiary's signature missing"
    assert deadline_reached(datum, context), "deadline not reached"
    return None
