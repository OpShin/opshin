import subprocess
import tempfile
import types
import unittest

from opshin.contract_interface import discover_contract_module
from opshin.prelude import *
from .utils import eval_uplc_value


def make_tx_info(inputs, purpose, redeemer):
    return TxInfo(
        inputs=inputs,
        reference_inputs=[],
        outputs=[],
        fee=0,
        mint={},
        certificates=[],
        withdrawals={},
        validity_range=POSIXTimeRange(
            lower_bound=LowerBoundPOSIXTime(FinitePOSIXTime(0), TrueData()),
            upper_bound=UpperBoundPOSIXTime(PosInfPOSIXTime(), FalseData()),
        ),
        signatories=[],
        redeemers={purpose: redeemer},
        datums={},
        id=b"\x01" * 32,
        votes={},
        proposal_procedures=[],
        current_treasury_amount=NoValue(),
        treasury_donation=NoValue(),
    )


def make_spending_context(datum, redeemer):
    out_ref = TxOutRef(id=b"\x02" * 32, idx=0)
    purpose = Spending(tx_out_ref=out_ref)
    inputs = [
        TxInInfo(
            out_ref=out_ref,
            resolved=TxOut(
                address=Address(
                    payment_credential=ScriptCredential(b"\x03" * 28),
                    staking_credential=NoStakingCredential(),
                ),
                value={b"": {b"": 0}},
                datum=SomeOutputDatum(datum),
                reference_script=NoScriptHash(),
            ),
        )
    ]
    return ScriptContext(
        transaction=make_tx_info(inputs, purpose, redeemer),
        redeemer=redeemer,
        purpose=purpose,
    )


def make_minting_context(redeemer):
    purpose = Minting(policy_id=b"\x04" * 28)
    return ScriptContext(
        transaction=make_tx_info([], purpose, redeemer),
        redeemer=redeemer,
        purpose=purpose,
    )


CONTRACT_SOURCE = """
from opshin.prelude import *

@dataclass()
class Contract:
    offset: int

    def spend(self, datum: int, redeemer: int, context: ScriptContext) -> int:
        return datum + redeemer + self.offset

    def mint(self, redeemer: int, context: ScriptContext) -> int:
        return redeemer * self.offset
"""

COLLIDING_NAMES_CONTRACT_SOURCE = """
from opshin.prelude import *

@dataclass()
class Contract:
    context: int
    redeemer: int

    def mint(self, policy_redeemer: int, script_context: ScriptContext) -> int:
        return self.context + self.redeemer + policy_redeemer
"""


class ContractClassTests(unittest.TestCase):
    def test_contract_spend_dispatches_through_validator(self):
        ret = eval_uplc_value(CONTRACT_SOURCE, 7, make_spending_context(2, 3))
        self.assertEqual(ret, 12)

    def test_contract_mint_dispatches_through_validator(self):
        ret = eval_uplc_value(CONTRACT_SOURCE, 5, make_minting_context(4))
        self.assertEqual(ret, 20)

    def test_runtime_contract_discovery_builds_validator(self):
        module = types.ModuleType("contract_module")
        exec(CONTRACT_SOURCE, module.__dict__)
        contract_info = discover_contract_module(module)
        self.assertIsNotNone(contract_info)
        self.assertEqual(contract_info.purpose_names, ("spending", "minting"))
        self.assertEqual(contract_info.validator(3, make_minting_context(6)), 18)

    def test_contract_handles_parameter_name_collisions(self):
        ret = eval_uplc_value(
            COLLIDING_NAMES_CONTRACT_SOURCE,
            10,
            20,
            make_minting_context(7),
        )
        self.assertEqual(ret, 37)

    def test_main_compiles_contract_class_without_explicit_validator(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = f"{tmpdir}/contract.py"
            with open(contract_path, "w") as fp:
                fp.write(CONTRACT_SOURCE)
            result = subprocess.run(
                ["opshin", "compile", contract_path, '{"int": 5}'],
                capture_output=True,
                text=True,
                cwd=tmpdir,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
