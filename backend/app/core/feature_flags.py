import os
from typing import Dict

class FeatureFlags:
    def __init__(self):
        self._flags: Dict[str, bool] = {
            "AI_RECOMMENDATIONS": True,
            "OFFLINE_SCANNING": True,
            "RESERVED_SEATING": True,
            "WAITLIST": True,
            "TICKET_TRANSFER": True,
            "MAINTENANCE_MODE": False
        }

    def is_enabled(self, flag_name: str) -> bool:
        env_val = os.getenv(f"FLAG_{flag_name}")
        if env_val is not None:
            return env_val.lower() in ["true", "1", "yes"]
        return self._flags.get(flag_name, True)

    def set_flag(self, flag_name: str, enabled: bool):
        self._flags[flag_name] = enabled

    def get_all_flags(self) -> Dict[str, bool]:
        return {k: self.is_enabled(k) for k in self._flags.keys()}

feature_flags = FeatureFlags()
