import subprocess
import tempfile
import types
import unittest
import ast

from opshin.contract_interface import discover_contract_module
from opshin.prelude import *
from opshin.rewrite.rewrite_contract_methods import RewriteContractMethods
from opshin.util import CompilerError
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


def make_spending_context_without_datum(redeemer):
    out_ref = TxOutRef(id=b"\x05" * 32, idx=0)
    purpose = Spending(tx_out_ref=out_ref)
    inputs = [
        TxInInfo(
            out_ref=out_ref,
            resolved=TxOut(
                address=Address(
                    payment_credential=ScriptCredential(b"\x06" * 28),
                    staking_credential=NoStakingCredential(),
                ),
                value={b"": {b"": 0}},
                datum=NoOutputDatum(),
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

RAW_CONTRACT_SOURCE = """
from opshin.prelude import *

@dataclass()
class Contract:
    offset: int

    def raw(self, script_context: ScriptContext) -> int:
        redeemer: int = script_context.redeemer
        return self.offset + redeemer
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

INVALID_CONSTR_ID_CONTRACT_SOURCE = """
from opshin.prelude import *

@dataclass()
class Contract:
    CONSTR_ID = 0

    def raw(self, context: ScriptContext) -> None:
        pass
"""

INVALID_UNANNOTATED_FIELD_CONTRACT_SOURCE = """
from opshin.prelude import *

@dataclass()
class Contract:
    offset = 0

    def raw(self, context: ScriptContext) -> None:
        pass
"""

OPTIONAL_DATUM_CONTRACT_SOURCE = """
from typing import Union

from opshin.prelude import *

@dataclass()
class Contract:
    offset: int

    def spend(
        self, datum: Union[int, NoOutputDatum], redeemer: int, context: ScriptContext
    ) -> int:
        if isinstance(datum, NoOutputDatum):
            return self.offset - redeemer
        else:
            return datum + redeemer + self.offset
"""

OUTPUT_DATUM_CONTRACT_SOURCE = """
from opshin.prelude import *

@dataclass()
class Contract:
    def spend(self, datum: OutputDatum, redeemer: int, context: ScriptContext) -> int:
        if isinstance(datum, NoOutputDatum):
            return redeemer
        assert isinstance(datum, SomeOutputDatum)
        unwrapped_datum: int = datum.datum
        return unwrapped_datum + redeemer
"""

HELPER_METHOD_CONTRACT_SOURCE = """
from opshin.prelude import *

@dataclass()
class Contract:
    offset: int

    def add_offset(self, value: int) -> int:
        return self.offset + value

    def mint(self, redeemer: int, context: ScriptContext) -> int:
        return self.add_offset(redeemer)
"""


class ContractClassTests(unittest.TestCase):
    def test_contract_spend_dispatches_through_validator(self):
        ret = eval_uplc_value(CONTRACT_SOURCE, 7, make_spending_context(2, 3))
        self.assertEqual(ret, 12)

    def test_contract_mint_dispatches_through_validator(self):
        ret = eval_uplc_value(CONTRACT_SOURCE, 5, make_minting_context(4))
        self.assertEqual(ret, 20)

    def test_contract_raw_dispatches_through_validator(self):
        ret = eval_uplc_value(RAW_CONTRACT_SOURCE, 5, make_minting_context(4))
        self.assertEqual(ret, 9)

    def test_contract_spend_supports_optional_raw_datum(self):
        with_datum = eval_uplc_value(
            OPTIONAL_DATUM_CONTRACT_SOURCE, 5, make_spending_context(2, 3)
        )
        without_datum = eval_uplc_value(
            OPTIONAL_DATUM_CONTRACT_SOURCE, 5, make_spending_context_without_datum(3)
        )
        self.assertEqual(with_datum, 10)
        self.assertEqual(without_datum, 2)

    def test_contract_spend_supports_output_datum_annotation(self):
        with_datum = eval_uplc_value(
            OUTPUT_DATUM_CONTRACT_SOURCE, make_spending_context(2, 3)
        )
        without_datum = eval_uplc_value(
            OUTPUT_DATUM_CONTRACT_SOURCE, make_spending_context_without_datum(3)
        )
        self.assertEqual(with_datum, 5)
        self.assertEqual(without_datum, 3)

    def test_contract_helper_methods_are_lifted(self):
        ret = eval_uplc_value(HELPER_METHOD_CONTRACT_SOURCE, 5, make_minting_context(4))
        self.assertEqual(ret, 9)

    def test_runtime_contract_discovery_builds_validator(self):
        module = types.ModuleType("contract_module")
        exec(CONTRACT_SOURCE, module.__dict__)
        contract_info = discover_contract_module(module)
        self.assertIsNotNone(contract_info)
        self.assertEqual(contract_info.purpose_names, ("spending", "minting"))
        self.assertEqual(contract_info.validator(3, make_minting_context(6)), 18)

    def test_runtime_contract_discovery_builds_raw_validator(self):
        module = types.ModuleType("contract_module")
        exec(RAW_CONTRACT_SOURCE, module.__dict__)
        contract_info = discover_contract_module(module)
        self.assertIsNotNone(contract_info)
        self.assertEqual(contract_info.purpose_names, ("any",))
        self.assertEqual(contract_info.validator(3, make_minting_context(6)), 9)

    def test_runtime_contract_discovery_builds_optional_datum_validator(self):
        module = types.ModuleType("contract_module")
        exec(OPTIONAL_DATUM_CONTRACT_SOURCE, module.__dict__)
        contract_info = discover_contract_module(module)
        self.assertIsNotNone(contract_info)
        self.assertEqual(
            contract_info.validator(3, make_spending_context_without_datum(7)), -4
        )

    def test_contract_handles_parameter_name_collisions(self):
        ret = eval_uplc_value(
            COLLIDING_NAMES_CONTRACT_SOURCE,
            10,
            20,
            make_minting_context(7),
        )
        self.assertEqual(ret, 37)

    def test_contract_rejects_constr_id_definition(self):
        with self.assertRaises(CompilerError) as exc:
            eval_uplc_value(INVALID_CONSTR_ID_CONTRACT_SOURCE, make_minting_context(0))
        self.assertIsInstance(exc.exception.orig_err, AssertionError)

    def test_contract_rejects_unannotated_field_definition(self):
        with self.assertRaises(CompilerError) as exc:
            eval_uplc_value(
                INVALID_UNANNOTATED_FIELD_CONTRACT_SOURCE, make_minting_context(0)
            )
        self.assertIsInstance(exc.exception.orig_err, AssertionError)

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

    def test_runtime_contract_discovery_rejects_constr_id_definition(self):
        module = types.ModuleType("contract_module")
        exec(INVALID_CONSTR_ID_CONTRACT_SOURCE, module.__dict__)
        with self.assertRaises(AssertionError):
            discover_contract_module(module)

    def test_runtime_contract_discovery_rejects_unannotated_field_definition(self):
        module = types.ModuleType("contract_module")
        exec(INVALID_UNANNOTATED_FIELD_CONTRACT_SOURCE, module.__dict__)
        with self.assertRaises(AssertionError):
            discover_contract_module(module)

    def test_contract_rewrite_removes_contract_class(self):
        rewritten_module = RewriteContractMethods().visit(ast.parse(CONTRACT_SOURCE))
        self.assertFalse(
            any(
                isinstance(statement, ast.ClassDef) and statement.name == "Contract"
                for statement in rewritten_module.body
            )
        )
