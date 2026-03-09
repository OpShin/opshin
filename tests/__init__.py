import datetime
import hypothesis

from .uplc_patch import patch_uplc_ast_reprs

PLUTUS_VM_PROFILE = "plutus_vm"
patch_uplc_ast_reprs()
hypothesis.settings.register_profile(
    PLUTUS_VM_PROFILE, deadline=datetime.timedelta(seconds=2)
)
