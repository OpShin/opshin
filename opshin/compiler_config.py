from dataclasses import dataclass
from typing import Optional

import pluthon


@dataclass(frozen=True)
class CompilationConfig(pluthon.CompilationConfig):
    constant_folding: Optional[bool] = None
    allow_isinstance_anything: Optional[bool] = None
    force_three_params: Optional[bool] = None
    remove_dead_code: Optional[bool] = None


# The default configuration for the compiler
OPT_O0_CONFIG = (
    CompilationConfig()
    .update(pluthon.OPT_O0_CONFIG)
    .update(
        constant_folding=False,
        remove_dead_code=False,
    )
)
OPT_O1_CONFIG = (
    CompilationConfig()
    .update(OPT_O0_CONFIG)
    .update(pluthon.OPT_O1_CONFIG)
    .update(
        remove_dead_code=True,
    )
)
OPT_O2_CONFIG = (
    CompilationConfig()
    .update(OPT_O1_CONFIG)
    .update(pluthon.OPT_O2_CONFIG)
    .update(
        constant_folding=True,
    )
)
OPT_O3_CONFIG = (
    CompilationConfig().update(pluthon.OPT_O3_CONFIG).update(OPT_O2_CONFIG).update()
)
OPT_CONFIGS = [OPT_O0_CONFIG, OPT_O1_CONFIG, OPT_O2_CONFIG, OPT_O3_CONFIG]

DEFAULT_CONFIG = CompilationConfig(
    allow_isinstance_anything=False,
    force_three_params=False,
).update(OPT_O1_CONFIG)

ARGPARSE_ARGS = pluthon.ARGPARSE_ARGS.copy()
ARGPARSE_ARGS.update(
    {
        "constant_folding": {
            "__alts__": ["--cf"],
            "help": "Enables experimental constant folding, including propagation and code execution.",
        },
        "allow_isinstance_anything": {
            "help": "Enables the use of isinstance(x, D) in the contract where x is of type Anything. This is not recommended as it only checks the constructor id and not the actual type of the data.",
        },
        "force_three_params": {
            "__alts__": ["--ftp"],
            "help": "Enforces that the contract is always called with three virtual parameters on-chain. Enable if the script should support spending and other purposes.",
        },
        "remove_dead_code": {
            "help": "Removes dead code and variables from the contract. Should be enabled for non-debugging purposes.",
        },
    }
)
for k in ARGPARSE_ARGS:
    assert (
        k in DEFAULT_CONFIG.__dict__
    ), f"Key {k} not found in CompilationConfig.__dict__"
