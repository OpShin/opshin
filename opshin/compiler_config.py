from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CompilationConfig:
    constant_folding: Optional[bool] = None
    allow_isinstance_anything: Optional[bool] = None
    compress_patterns: Optional[bool] = None
    force_three_params: Optional[bool] = None
    remove_dead_code: Optional[bool] = None

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
OPT_O0_CONFIG = CompilationConfig(
    constant_folding=False,
    compress_patterns=False,
    remove_dead_code=False,
)
OPT_O1_CONFIG = CompilationConfig(
    constant_folding=False,
    compress_patterns=True,
    remove_dead_code=True,
)
OPT_O2_CONFIG = CompilationConfig(
    constant_folding=True,
    compress_patterns=True,
    remove_dead_code=True,
)
OPT_O3_CONFIG = CompilationConfig(
    constant_folding=True,
    compress_patterns=True,
    remove_dead_code=True,
)
OPT_CONFIGS = [OPT_O0_CONFIG, OPT_O1_CONFIG, OPT_O2_CONFIG, OPT_O3_CONFIG]

DEFAULT_CONFIG = CompilationConfig(
    allow_isinstance_anything=False,
    force_three_params=False,
).update(OPT_O1_CONFIG)


ARGPARSE_ARGS = {
    "constant_folding": {
        "__alts__": ["-cf"],
        "action": "store_true",
        "help": "Enables experimental constant folding, including propagation and code execution.",
    },
    "allow_isinstance_anything": {
        "action": "store_true",
        "help": "Enables the use of isinstance(x, D) in the contract where x is of type Anything. This is not recommended as it only checks the constructor id and not the actual type of the data.",
    },
    "compress_patterns": {
        "action": "store_true",
        "help": "Enables the compression of re-occurring code patterns. Can reduce memory and CPU steps but increases the size of the compiled contract.",
    },
    "force_three_params": {
        "__alts__": ["-ftp"],
        "action": "store_true",
        "help": "Enforces that the contract is always called with three virtual parameters on-chain. Enable if the script should support spending and other purposes.",
    },
    "remove_dead_code": {
        "action": "store_true",
        "help": "Removes dead code and variables from the contract. Should be enabled for non-debugging purposes.",
    },
}
for k in ARGPARSE_ARGS:
    assert (
        k in DEFAULT_CONFIG.__dict__
    ), f"Key {k} not found in CompilationConfig.__dict__"
