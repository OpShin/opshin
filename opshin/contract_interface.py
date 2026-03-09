import dataclasses
import inspect
import typing

from .ledger.api_v3 import Minting, Publishing, Proposing, Spending, Voting, Withdrawing
from .prelude import (
    NoOutputDatum,
    ScriptContext,
    SomeOutputDatum,
    SomeOutputDatumHash,
)


@dataclasses.dataclass(frozen=True)
class ContractMethodSpec:
    method_name: str
    purpose_class: typing.Optional[type]
    purpose_name: str
    onchain_argument_count: int


CONTRACT_METHOD_SPECS = (
    ContractMethodSpec("raw", None, "any", 1),
    ContractMethodSpec("spend", Spending, "spending", 3),
    ContractMethodSpec("mint", Minting, "minting", 2),
    ContractMethodSpec("withdraw", Withdrawing, "rewarding", 2),
    ContractMethodSpec("publish", Publishing, "certifying", 2),
    ContractMethodSpec("vote", Voting, "voting", 2),
    ContractMethodSpec("propose", Proposing, "proposing", 2),
)

CONTRACT_METHOD_SPEC_MAP = {
    contract_method.method_name: contract_method
    for contract_method in CONTRACT_METHOD_SPECS
}


@dataclasses.dataclass(frozen=True)
class ContractMethodDetails:
    spec: ContractMethodSpec
    method: typing.Callable
    argument_names: typing.Tuple[str, ...]
    datum_type: typing.Optional[type]
    redeemer_type: typing.Optional[type]
    return_type: typing.Any


def _annotation_union_members(annotation: typing.Any) -> typing.Tuple[typing.Any, ...]:
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        return typing.get_args(annotation)
    return ()


def _datum_loading_strategy(annotation: typing.Any) -> str:
    union_members = _annotation_union_members(annotation)
    if not union_members:
        return "unsafe_raw"
    if NoOutputDatum not in union_members:
        return "unsafe_raw"
    attachment_types = {NoOutputDatum, SomeOutputDatum, SomeOutputDatumHash}
    if all(member in attachment_types for member in union_members):
        return "attachment"
    return "optional_raw"


def _resolve_spent_output(context: ScriptContext):
    purpose = context.purpose
    assert isinstance(
        purpose, Spending
    ), "Contract spend entrypoints require a spending script context."
    return [
        tx_input.resolved
        for tx_input in context.transaction.inputs
        if tx_input.out_ref == purpose.tx_out_ref
    ][0]


def _resolve_output_datum(context: ScriptContext):
    attached_datum = _resolve_spent_output(context).datum
    if isinstance(attached_datum, SomeOutputDatumHash):
        return SomeOutputDatum(context.transaction.datums[attached_datum.datum_hash])
    return attached_datum


def _resolve_output_datum_unsafe(context: ScriptContext):
    attached_datum = _resolve_output_datum(context)
    if isinstance(attached_datum, SomeOutputDatum):
        return attached_datum.datum
    assert False, "No datum was attached to the UTxO being spent by this Contract."


@dataclasses.dataclass(frozen=True)
class ContractModuleInfo:
    validator: typing.Callable
    parameter_types: typing.List[typing.Tuple[str, typing.Any]]
    method_details: typing.Tuple[ContractMethodDetails, ...]

    @property
    def purpose_names(self) -> typing.Tuple[str, ...]:
        return tuple(detail.spec.purpose_name for detail in self.method_details)

    @property
    def datum_type(self) -> typing.Optional[typing.Tuple[str, typing.Any]]:
        spending_methods = [
            detail
            for detail in self.method_details
            if detail.spec.method_name == "spend"
        ]
        if not spending_methods:
            return None
        detail = spending_methods[0]
        if detail.datum_type is inspect.Signature.empty:
            return None
        return ("datum", detail.datum_type)

    @property
    def redeemer_type(self) -> typing.Optional[typing.Tuple[str, typing.Any]]:
        redeemer_types = []
        for detail in self.method_details:
            if detail.spec.method_name == "raw":
                continue
            if detail.redeemer_type is inspect.Signature.empty:
                return None
            redeemer_types.append(detail.redeemer_type)
        if not redeemer_types:
            return None
        first = redeemer_types[0]
        if any(redeemer_type != first for redeemer_type in redeemer_types[1:]):
            return None
        return ("redeemer", first)


def _contract_parameter_types(
    contract_class: type,
) -> typing.List[typing.Tuple[str, typing.Any]]:
    assert (
        "CONSTR_ID" not in contract_class.__dict__
    ), "Contract classes must not define CONSTR_ID."
    annotations = inspect.get_annotations(contract_class)
    unannotated_fields = [
        name
        for name, value in contract_class.__dict__.items()
        if not name.startswith("__")
        and name not in annotations
        and name not in CONTRACT_METHOD_SPEC_MAP
        and not inspect.isfunction(value)
        and not isinstance(value, (staticmethod, classmethod))
    ]
    assert (
        not unannotated_fields
    ), "Contract fields must be annotated; unannotated Contract fields are not supported."
    return list(annotations.items())


def _method_annotations(
    method: typing.Callable, onchain_argument_count: int
) -> typing.Tuple[typing.Tuple[str, ...], typing.Any, typing.Any]:
    signature = inspect.signature(method)
    parameters = list(signature.parameters.values())
    assert (
        parameters
    ), f"Contract method '{method.__name__}' must accept self as first parameter."
    assert (
        parameters[0].name == "self"
    ), f"Contract method '{method.__name__}' must accept self as first parameter."
    expected_parameter_count = onchain_argument_count + 1
    assert len(parameters) == expected_parameter_count, (
        f"Contract method '{method.__name__}' must accept self plus "
        f"{onchain_argument_count} on-chain parameters."
    )
    method_parameters = parameters[1:]
    context_parameter = method_parameters[-1]
    if context_parameter.annotation is not inspect.Signature.empty:
        assert (
            context_parameter.annotation == ScriptContext
        ), f"Contract method '{method.__name__}' must annotate context as ScriptContext."
    datum_type = None
    redeemer_type = None
    if onchain_argument_count == 3:
        datum_type = method_parameters[0].annotation
        redeemer_type = method_parameters[1].annotation
    elif onchain_argument_count == 2:
        redeemer_type = method_parameters[0].annotation
    return (
        tuple(parameter.name for parameter in method_parameters),
        datum_type,
        redeemer_type,
    )


def _make_unique_name(preferred_name: str, used_names: typing.Set[str]) -> str:
    if preferred_name not in used_names:
        return preferred_name
    suffix = 0
    while f"{preferred_name}_{suffix}" in used_names:
        suffix += 1
    return f"{preferred_name}_{suffix}"


def _build_contract_validator(
    contract_class: type,
    parameter_types: typing.List[typing.Tuple[str, typing.Any]],
    method_details: typing.Tuple[ContractMethodDetails, ...],
):
    context_parameter_name = _make_unique_name(
        method_details[0].argument_names[-1],
        {field_name for field_name, _ in parameter_types},
    )

    def validator(*args):
        contract_parameter_count = len(parameter_types)
        contract = contract_class(*args[:contract_parameter_count])
        context = args[contract_parameter_count]
        raw_methods = [
            detail for detail in method_details if detail.spec.method_name == "raw"
        ]
        if raw_methods:
            assert (
                len(raw_methods) == 1
            ), "Contract may only define one raw entrypoint method."
            return raw_methods[0].method(contract, context)
        purpose = context.purpose
        for detail in method_details:
            assert (
                detail.spec.purpose_class is not None
            ), "Non-raw Contract entrypoint methods must define a script purpose."
            if not isinstance(purpose, detail.spec.purpose_class):
                continue
            if detail.spec.method_name == "spend":
                datum_loading_strategy = _datum_loading_strategy(detail.datum_type)
                if datum_loading_strategy == "attachment":
                    datum = _resolve_output_datum(context)
                elif datum_loading_strategy == "optional_raw":
                    attached_datum = _resolve_output_datum(context)
                    if isinstance(attached_datum, SomeOutputDatum):
                        datum = attached_datum.datum
                    else:
                        datum = attached_datum
                else:
                    datum = _resolve_output_datum_unsafe(context)
                return detail.method(contract, datum, context.redeemer, context)
            return detail.method(contract, context.redeemer, context)
        assert False, "Unsupported script purpose for Contract"

    validator.__name__ = "validator"
    return_annotations = [detail.return_type for detail in method_details]
    if return_annotations and any(
        return_type != return_annotations[0] for return_type in return_annotations[1:]
    ):
        raise AssertionError(
            "All Contract entrypoint methods must have the same return annotation."
        )
    validator.__signature__ = inspect.Signature(
        parameters=[
            inspect.Parameter(
                name=field_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=field_type,
            )
            for field_name, field_type in parameter_types
        ]
        + [
            inspect.Parameter(
                name=context_parameter_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=ScriptContext,
            )
        ],
        return_annotation=(
            return_annotations[0] if return_annotations else inspect.Signature.empty
        ),
    )
    validator.__annotations__ = {
        field_name: field_type for field_name, field_type in parameter_types
    }
    validator.__annotations__[context_parameter_name] = ScriptContext
    if return_annotations and return_annotations[0] is not inspect.Signature.empty:
        validator.__annotations__["return"] = return_annotations[0]
    return validator


def discover_contract_module(module) -> typing.Optional[ContractModuleInfo]:
    validator = getattr(module, "validator", None)
    if callable(validator):
        return None
    contract_class = getattr(module, "Contract", None)
    if contract_class is None or not inspect.isclass(contract_class):
        return None
    parameter_types = _contract_parameter_types(contract_class)
    method_details = []
    for spec in CONTRACT_METHOD_SPECS:
        method = getattr(contract_class, spec.method_name, None)
        if method is None:
            continue
        argument_names, datum_type, redeemer_type = _method_annotations(
            method, spec.onchain_argument_count
        )
        method_details.append(
            ContractMethodDetails(
                spec=spec,
                method=method,
                argument_names=argument_names,
                datum_type=datum_type,
                redeemer_type=redeemer_type,
                return_type=inspect.signature(method).return_annotation,
            )
        )
    if not method_details:
        return None
    raw_methods = [
        detail for detail in method_details if detail.spec.method_name == "raw"
    ]
    if raw_methods:
        assert (
            len(method_details) == 1
        ), "Contract may define either raw or purpose-specific entrypoints, not both."
    generated_validator = _build_contract_validator(
        contract_class,
        parameter_types,
        tuple(method_details),
    )
    return ContractModuleInfo(
        validator=generated_validator,
        parameter_types=parameter_types,
        method_details=tuple(method_details),
    )
