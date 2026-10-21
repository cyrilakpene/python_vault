import os
import pwd
from typing import Any

from interface.report_status import report_status  # type: ignore[import-not-found]
from security.runtime_context import log_path  # type: ignore[import-not-found]


# PRIVILEGED GATEKEEPER: USER OWNERSHIP VERIFICATION ENGINE
# Validates that a target file or directory is exclusively owned by the invoking runtime user.
# Prevents security exploits where elevated privileges interact with unauthorized or foreign user assets.
def verify_owner(file_path: str, ctx: dict[str, Any]) -> bool:
    """Validates that the file or directory at 'file_path' is owned by the
    user who invoked the script (ORIGINAL_USER).

    This prevents the privileged root process from accidentally or
    maliciously interacting with files belonging to other users.

    Args:
        file_path (str): Target filesystem path string to inspect for ownership verification.
        ctx: dict[str, Any]: Runtime context dictionary containing environment details, paths, and user info.

    Returns:
        bool: True if the asset is owned by the executing user profile, False otherwise.
    """
    try:
        # SYMLINK RACE CONDITION SAFEGUARD & METADATA INSPECTION
        # Uses os.lstat() to evaluate target metadata directly without resolving or following symbolic links,
        # mitigating arbitrary file traversal and spoofing vectors.
        file_stat = os.lstat(file_path)

        # IDENTITY MATCH EVALUATION
        # Compares the filesystem object's owner UID against the authenticated runtime user UID profile.
        original_user = ctx.get("user", "")
        if file_stat.st_uid == pwd.getpwnam(original_user).pw_uid:
            return True

        # SECURITY AUDIT LOGGING: OWNERSHIP MISMATCH DETECTION
        # Emits a secure diagnostic warning to standard error when an asset ownership violation occurs.
        report_status(
            state="warn",
            message=f"Security Error: You do not own the file {file_path}",
            log_path=log_path,
        )
        return False

    except Exception as e:
        # EXCEPTION TRAPPING & FAULT TOLERANCE
        # Captures filesystem access violations, missing path states, or permission denials during stat evaluation.
        report_status(
            state="warn",
            message=f"Error accessing file for ownership check: {e}",
            log_path=log_path,
        )
        return False
