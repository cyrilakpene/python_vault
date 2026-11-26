"""Public interface for the input collection, validation, and exception handling module."""

from .user_input import user_input
from .security import verify_password
from .exceptions import UserCancelError, MaxRetriesExceededError

# PUBLIC EXPORTS: STABLE PACKAGE API SURFACE
# Exposes the primary input entry point, password verification helper, and control-flow exceptions.
__all__ = [
    "user_input",
    "verify_password",
    "UserCancelError",
    "MaxRetriesExceededError",
]
