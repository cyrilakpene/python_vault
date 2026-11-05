import os
import pwd
import grp

from .constants import report_status, LogContext  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: USER IDENTITY & ENVIRONMENT RESOLUTION
# This utility resolves the human user's username, UID, GID, and home directory,
# featuring robust fallback mechanisms for sudo environments, login shells, and missing password database entries.
# [>] EXECUTING USER IDENTITY RESOLUTION
def resolve_user_identity() -> tuple[str, int, int, str]:
    """
    Resolves human user name, UID, GID, and home directory.

    Returns:
        tuple[str, int, int, str]: A tuple containing the username, user ID (UID), group ID (GID), and home directory path.
    """
    # USERNAME RESOLUTION & FALLBACK CHAIN
    # Attempts to resolve the active human user via SUDO_USER, login sessions, or password database records,
    # falling back to environment variables or 'root' if necessary.
    try:
        user = (
            os.environ.get("SUDO_USER")
            or os.getlogin()
            or pwd.getpwuid(os.getuid()).pw_name
        )
    except (KeyError, AttributeError, OSError):
        user = os.environ.get("USER") or "root"

    # PASSWORD DATABASE LOOKUP & SYSTEM IDENTITY EXTRACTION
    # Queries the system password database for the resolved username to retrieve standard UID, GID, and home path.
    try:
        pw_info = pwd.getpwnam(user)
        return user, pw_info.pw_uid, pw_info.pw_gid, pw_info.pw_dir
    except KeyError:
        # EMERGENCY FALLBACK ROUTINE
        # Falls back to current process IDs and expanded home directories if the username is not found in the password database.
        return (
            user,
            os.getuid(),
            os.getgid(),
            os.path.expanduser("~"),
        )


# SYSTEM UTILITIES SUBSYSTEM: POSIX GROUP VALIDATION & GID RESOLUTION
# This utility validates the existence of a target POSIX group on the system,
# returning its GID or gracefully reporting a failure and exiting with instructions.
# [>] EXECUTING POSIX GROUP VALIDATION
def validate_group(
    human_user: str | None, target_group: str, session_path: str | None
) -> int:
    """
    Validates the target POSIX group existence and returns its GID.

    Args:
        human_user (str | None): The resolved human username to audit.
        target_group (str): The name of the POSIX group to validate.
        session_path (str | None): The file path for logging error status reports, if any.

    Returns:
        int: The Group ID (GID) of the validated POSIX group.

    Raises:
        SystemExit: If the target group does not exist on the system.
    """
    # POSIX GROUP LOOKUP & GID EXTRACTION
    # Attempts to query the system group database for the target group name
    # and returns its associated Group ID (GID) upon success.
    try:
        group_info = grp.getgrnam(target_group)
        return group_info.gr_gid
    except KeyError:
        # GROUP MISSING ERROR HANDLING & SYSTEM EXIT HINT
        # Reports the missing group failure, provides a helpful CLI remediation hint,
        # and terminates the process with a non-zero exit code.
        report_status(
            state="fail",
            message=f"Required group {target_group!r} missing from system.",
            context=LogContext(
                component="security.runtimecontext",
                log_path=session_path,
                silent=False,
                trace_id="runtimecontext",
                actor=human_user,
                payload={"target_group": target_group},
            ),
        )
        report_status(
            state="item",
            message=f"HINT: Create it using 'sudo groupadd {target_group}'",
            context=LogContext(
                component="security.runtimecontext",
                log_path=session_path,
                silent=True,
                trace_id="runtimecontext",
                actor=human_user,
                payload={"target_group": target_group},
            ),
        )
        raise SystemExit(1)
