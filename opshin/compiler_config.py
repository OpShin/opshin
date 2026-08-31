from dataclasses import dataclass
from typing import Optional

import pluthon


@dataclass(frozen=True)
class CompilationConfig(pluthon.CompilationConfig):
    constant_folding: Optional[bool] = None
    allow_isinstance_anything: Optional[bool] = None
    remove_dead_code: Optional[bool] = None
    fast_access_skip: Optional[int] = None
    expand_union_types: Optional[bool] = None
    wrap_output: Optional[bool] = None
    unwrap_input: Optional[bool] = None
    dict_last_value_wins: Optional[bool] = None
    optimize_bool_only_ops: Optional[bool] = None
    optimize_selective_narrowing: Optional[bool] = None


# The default configuration for the compiler
OPT_O0_CONFIG = (
    CompilationConfig()
    .update(pluthon.OPT_O0_CONFIG)
    .update(
        constant_folding=False,
        remove_dead_code=False,
        dict_last_value_wins=True,
        optimize_bool_only_ops=False,
        optimize_selective_narrowing=False,
    )
)
OPT_O1_CONFIG = (
    CompilationConfig()
    .update(OPT_O0_CONFIG)
    .update(pluthon.OPT_O1_CONFIG)
    .update(
        remove_dead_code=True,
        optimize_bool_only_ops=True,
        optimize_selective_narrowing=True,
    )
)
OPT_O2_CONFIG = (
    CompilationConfig()
    .update(OPT_O1_CONFIG)
    .update(pluthon.OPT_O2_CONFIG)
    .update(
        constant_folding=True,
        fast_access_skip=5,
    )
)
OPT_O3_CONFIG = (
    CompilationConfig()
    .update(OPT_O2_CONFIG)
    .update(pluthon.OPT_O3_CONFIG)
    .update(dict_last_value_wins=False)
)
OPT_CONFIGS = [OPT_O0_CONFIG, OPT_O1_CONFIG, OPT_O2_CONFIG, OPT_O3_CONFIG]

DEFAULT_CONFIG = CompilationConfig(
    allow_isinstance_anything=False,
    expand_union_types=False,
    wrap_output=False,
    unwrap_input=True,
).update(OPT_O2_CONFIG)

ARGPARSE_ARGS = pluthon.ARGPARSE_ARGS.copy()
ARGPARSE_ARGS.update(
    {
        "constant_folding": {
            "__alts__": ["--cf"],
            "help": "Enables experimental constant folding, including constant propagation and code execution.",
        },
        "allow_isinstance_anything": {
            "help": "Enables the use of isinstance(x, D) in the contract where x is of type Anything. This is not recommended as it only checks the constructor id and not the actual type of the data.",
        },
        "remove_dead_code": {
            "help": "Removes dead code and variables from the contract. Should be enabled for non-debugging purposes.",
        },
        "fast_access_skip": {
            "help": "How many steps to skip for fast list index access, default None means no steps are skipped (useful if long lists are common).",
            "type": int,
        },
        "expand_union_types": {
            "__alts__": ["--eut"],
            "help": "Expand functions with Union type arguments into monomorphic variants (e.g. foo(Union[int, bytes]) -> foo_i(int), foo_b(bytes)). This should allow the compiler to optimise away redundant type checks when argument types are known at compile time. This is an O3-level optimisation and may increase script size significantly.",
        },
        "wrap_output": {
            "__alts__": ["--wo"],
            "help": "Wraps the output of the validator in PlutusData. This is useful for exporting library functions that return non-None values as validators.",
        },
        "unwrap_input": {
            "__alts__": ["--wi"],
            "help": "Unwraps the input of the validator from PlutusData. Disabling this is useful for exporting library functions that take builtin data as input.",
        },
        "dict_last_value_wins": {
            "help": "Enforces Python's ordered, last-value-wins semantics for duplicate dictionary keys. Disabling this saves script size and execution cost but retains duplicate map entries. Disabled by -O3.",
        },
        "optimize_bool_only_ops": {
            "help": "Compiles and/or expressions directly to booleans when their operand value cannot escape. Enabled at -O1 and above.",
        },
        "optimize_selective_narrowing": {
            "help": "Caches repeatedly used values narrowed by isinstance. Enabled at -O1 and above.",
        },
    }
)
for k in ARGPARSE_ARGS:
    assert (
        k in DEFAULT_CONFIG.__dict__
    ), f"Key {k} not found in CompilationConfig.__dict__"
