import dataclasses
import typing

import pycardano
import uplc.ast as uplc_ast
from pycardano import PlutusData
from uplc import eval as uplc_eval

from ..builder import _compile


@dataclasses.dataclass
class Unit(PlutusData):
    CONSTR_ID = 0


def eval_uplc(
    source_code: str,
    *args: typing.Union[pycardano.Datum, uplc_ast.Constant],
    contract_file: str = "<unknown>",
    force_three_params=False,
    validator_function_name="validator",
    optimize_patterns=True,
    remove_dead_code=True,
    constant_folding=False,
    allow_isinstance_anything=False,
):
    code = _compile(
        source_code,
        *args,
        contract_file=contract_file,
        force_three_params=force_three_params,
        validator_function_name=validator_function_name,
        optimize_patterns=optimize_patterns,
        remove_dead_code=remove_dead_code,
        constant_folding=constant_folding,
        allow_isinstance_anything=allow_isinstance_anything,
    )
    return uplc_eval(code)


def eval_uplc_value(
    source_code: str,
    *args: typing.Union[pycardano.Datum, uplc_ast.Constant],
    contract_file: str = "<unknown>",
    force_three_params=False,
    validator_function_name="validator",
    optimize_patterns=True,
    remove_dead_code=True,
    constant_folding=False,
    allow_isinstance_anything=False,
):
    return eval_uplc(
        source_code,
        *args,
        contract_file=contract_file,
        force_three_params=force_three_params,
        validator_function_name=validator_function_name,
        optimize_patterns=optimize_patterns,
        remove_dead_code=remove_dead_code,
        constant_folding=constant_folding,
        allow_isinstance_anything=allow_isinstance_anything,
    ).value
