import datetime
import hypothesis

PLUTUS_VM_PROFILE = "plutus_vm"
hypothesis.settings.register_profile(
    PLUTUS_VM_PROFILE, deadline=datetime.timedelta(seconds=1)
)
