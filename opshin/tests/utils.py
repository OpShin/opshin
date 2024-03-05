import dataclasses
import functools
import typing

import pycardano
import uplc.ast as uplc_ast
from pycardano import PlutusData
from uplc import eval as uplc_eval

from .. import DEFAULT_CONFIG
from ..builder import _compile


@dataclasses.dataclass
class Unit(PlutusData):
    CONSTR_ID = 0


def eval_uplc(
    source_code: str,
    *args: typing.Union[pycardano.Datum, uplc_ast.Constant],
    contract_file: str = "<unknown>",
    validator_function_name="validator",
    config=DEFAULT_CONFIG,
):
    code = _compile(
        source_code,
        *args,
        contract_file=contract_file,
        validator_function_name=validator_function_name,
        config=config,
    )
    return uplc_eval(code)


def eval_uplc_value(
    source_code: str,
    *args: typing.Union[pycardano.Datum, uplc_ast.Constant],
    contract_file: str = "<unknown>",
    validator_function_name="validator",
    config=DEFAULT_CONFIG,
):
    return eval_uplc(
        source_code,
        *args,
        contract_file=contract_file,
        validator_function_name=validator_function_name,
        config=config,
    ).value
