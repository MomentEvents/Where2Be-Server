from api.version.ver_1_0_0.auth.permissions import is_real_user
from api.version.ver_1_0_0.auth.permissions import is_user_privileged
from api.version.ver_1_0_0.auth.permissions import is_user_privileged_for_user
from api.version.ver_1_0_0.auth.permissions import is_user_privileged_for_event

__all__ = [
    "is_real_user",
    "is_user_privileged",
    "is_user_privileged_for_user",
    "is_user_privileged_for_event"
]
