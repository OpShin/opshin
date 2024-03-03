from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CompilationConfig:
    constant_folding: Optional[bool] = None
    allow_isinstance_anything: Optional[bool] = None
    optimize_patterns: Optional[bool] = None
    force_three_params: Optional[bool] = None

    def update(self, other: "CompilationConfig") -> "CompilationConfig":
        own_dict = self.__dict__
        other_dict = other.__dict__
        return CompilationConfig(
            **{
                k: other_dict[k] if other_dict[k] is not None else own_dict[k]
                for k in own_dict
            }
        )


# The default configuration for the compiler
DEFAULT_CONFIG = CompilationConfig(
    constant_folding=False,
    allow_isinstance_anything=False,
    optimize_patterns=False,
    force_three_params=False,
)

OPT_O0_CONFIG = CompilationConfig(
    constant_folding=False,
    optimize_patterns=False,
)
OPT_O1_CONFIG = CompilationConfig(
    constant_folding=False,
    optimize_patterns=True,
)
OPT_O2_CONFIG = CompilationConfig(
    constant_folding=True,
    optimize_patterns=True,
)
OPT_O3_CONFIG = CompilationConfig(
    constant_folding=True,
    optimize_patterns=True,
)
OPT_CONFIGS = [OPT_O0_CONFIG, OPT_O1_CONFIG, OPT_O2_CONFIG, OPT_O3_CONFIG]

print(DEFAULT_CONFIG.__dict__)

ARGPARSE_KWARGS = {
    "constant_folding": {
        "action": "store_true",
        "help": "Enables experimental constant folding, including propagation and code execution.",
    },
    "allow_isinstance_anything": {
        "action": "store_true",
        "help": "Enables the use of isinstance(x, D) in the contract where x is of type Anything. This is not recommended as it only checks the constructor id and not the actual type of the data.",
    },
    "no_optimize_patterns": {
        "action": "store_true",
        "help": "Disables the compression of re-occurring code patterns. Can reduce memory and CPU steps but increases the size of the compiled contract.",
    },
    "force_three_params": {
        "action": "store_true",
        "help": "Enforces that the contract is always called with three virtual parameters on-chain. Enable if the script should support spending and other purposes.",
    },
}
for k in ARGPARSE_KWARGS:
    assert (
        k in DEFAULT_CONFIG.__dict__
    ), f"Key {k} not found in CompilationConfig.__dict__"
