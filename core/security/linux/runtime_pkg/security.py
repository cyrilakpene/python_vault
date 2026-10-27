import os
import pwd
from typing import Any

from .constants import report_status
from .identity import validate_group


# SYSTEM UTILITIES SUBSYSTEM: SECURITY CONTEXT AUDIT & PRIVILEGE MANAGEMENT
# This utility audits user identities, UIDs, GIDs, effective root privileges, home directories,
# and GUI display environment pointers for secure privilege dropping and environment preservation.
# [>] EXECUTING SECURITY CONTEXT AUDIT
def audit_security_context(
    human_user: str | None, target_group: str, session_path: str | None
) -> dict[str, Any]:
    """
    Audits UIDs, GIDs, effective privileges, and display context pointers.

    Args:
        human_user (str | None): The resolved human username to audit.
        target_group (str): The target POSIX group name required by the session.
        session_path (str | None): The file path for logging status reports, if any.

    Returns:
        dict[str, Any]: A dictionary containing audited security attributes, IDs, and display environment pointers.

    Raises:
        ValueError: If the human user identity has not been resolved.
        SystemExit: If the specified human user does not exist on the system.
    """
    # TASK REPORTING & IDENTITY VALIDATION
    # Reports the start of the security audit task and validates that the human user identity has been resolved.
    report_status(
        state="task",
        message="IDENTITY PIVOT: ESCAPING PRIVILEGE ESCALATION.",
        log_path=session_path,
        silent=True,
    )

    if not human_user:
        raise ValueError(
            "Human user identity has not been resolved yet. Run resolve_session_path() first."
        )

    # PASSWORD DATABASE LOOKUP & USER VERIFICATION
    # Queries the password database for user information, raising a SystemExit if the user is missing.
    try:
        user_info = pwd.getpwnam(human_user)
    except KeyError:
        report_status(
            state="fail",
            message=f"Security context error: User {human_user!r} does not exist.",
            log_path=session_path,
        )
        raise SystemExit(1)

    # GROUP VALIDATION & PRIVILEGE CHECK
    # Validates the target POSIX group and checks whether the current process is running with root privileges (EUID 0).
    target_gid = validate_group(target_group, session_path)
    is_privileged = os.geteuid() == 0

    # HOME DIRECTORY ACCESSIBILITY CHECK
    # Issues a warning status report if the resolved home directory path is missing or inaccessible.
    if not os.path.isdir(user_info.pw_dir):
        report_status(
            state="warn",
            message=f"WARNING: Resolved home {user_info.pw_dir!r} is inaccessible.",
            log_path=session_path,
        )

    # DISPLAY CONTEXT ENVIRONMENT GATHERING
    # Captures GUI display and desktop session environment pointers for graphic subsystem continuity.
    display_context = {
        "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY"),
        "DISPLAY": os.environ.get("DISPLAY"),
        "XAUTHORITY": os.environ.get("XAUTHORITY"),
        "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR"),
    }

    # SECURITY AUDIT DICTIONARY ASSEMBLY & RETURN
    # Compiles and returns the comprehensive security context dictionary.
    return {
        "user": human_user,
        "uid": user_info.pw_uid,
        "gid": user_info.pw_gid,
        "home": user_info.pw_dir,
        "target_group": target_group,
        "target_gid": target_gid,
        "is_privileged": is_privileged,
        "display_context": display_context,
    }
