import dataclasses

import pycardano
from pycardano import PlutusData
from uplc import eval as uplc_eval

from ..builder import _compile


@dataclasses.dataclass
class Unit(PlutusData):
    CONSTR_ID = 0


def eval_uplc(
    source_code: str,
    *args: pycardano.Datum,
    contract_file: str = "<unknown>",
    force_three_params=False,
    validator_function_name="validator",
    optimize_patterns=True,
):
    code = _compile(
        source_code,
        *args,
        contract_file=contract_file,
        force_three_params=force_three_params,
        validator_function_name=validator_function_name,
        optimize_patterns=optimize_patterns,
    )
    return uplc_eval(code)


def eval_uplc_value(
    source_code: str,
    *args: pycardano.Datum,
    contract_file: str = "<unknown>",
    force_three_params=False,
    validator_function_name="validator",
    optimize_patterns=True,
):
    return eval_uplc(
        source_code,
        *args,
        contract_file=contract_file,
        force_three_params=force_three_params,
        validator_function_name=validator_function_name,
        optimize_patterns=optimize_patterns,
    ).value
