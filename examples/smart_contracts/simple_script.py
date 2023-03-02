from eopsin.prelude import *


@dataclass()
class RequireSignature(PlutusData):
    CONSTR_ID = 0
    vkeyhash: bytes  # this is either a PubKeyHash or a VerificationKeyHash


@dataclass()
class RequireAllOf(PlutusData):
    CONSTR_ID = 1
    scripts: List[Datum]  # "Script"


@dataclass()
class RequireAnyOf(PlutusData):
    CONSTR_ID = 2
    scripts: List[Datum]  # "Script"


@dataclass()
class RequireMOf(PlutusData):
    CONSTR_ID = 3
    num: int
    scripts: List[Datum]  # "Script"


@dataclass()
class RequireBefore(PlutusData):
    CONSTR_ID = 4
    unixtimestamp: int


@dataclass()
class RequireAfter(PlutusData):
    CONSTR_ID = 5
    unixtimestamp: int


Script = Union[
    RequireSignature,
    RequireMOf,
    RequireAnyOf,
    RequireAllOf,
    RequireAfter,
    RequireBefore,
]


def validate_script(
    script_raw: Datum, signatories: List[bytes], valid_range: POSIXTimeRange
) -> bool:
    script: Script = script_raw  # cast to Script in the type system to avoid recursive type definition
    if isinstance(script, RequireSignature):
        res = script.vkeyhash in signatories
    elif isinstance(script, RequireAllOf):
        res = all(
            [validate_script(s, signatories, valid_range) for s in script.scripts]
        )
    elif isinstance(script, RequireAnyOf):
        res = any(
            [validate_script(s, signatories, valid_range) for s in script.scripts]
        )
    elif isinstance(script, RequireMOf):
        res = (
            sum(
                [
                    1 if validate_script(s, signatories, valid_range) else 0
                    for s in script.scripts
                ]
            )
            >= script.num
        )
    elif isinstance(script, RequireBefore):
        res = valid_range.upper_bound < script.unixtimestamp
    elif isinstance(script, RequireAfter):
        res = valid_range.lower_bound > script.unixtimestamp
    else:
        assert False, "Invalid simple script passed"
    return res


# to fully emulate simple script behaviour, compile with --force-three-params
# the script is a contract parameter, pass it into the build command
def validator(
    script: Script, datum: None, redeemer: None, context: ScriptContext
) -> None:
    assert validate_script(
        script, context.tx_info.signatories, context.tx_info.valid_range
    ), "Simple Script validation failed!"
