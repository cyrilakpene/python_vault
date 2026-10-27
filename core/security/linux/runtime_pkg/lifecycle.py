import os
import time
from datetime import datetime


# SYSTEM UTILITIES SUBSYSTEM: SESSION PATH RESOLUTION & SECURE STORAGE PROVISIONING
# This utility provisions secure physical storage directories, generates timestamped session log files,
# and enforces proper file ownership via UID/GID chown calls when running with root privileges.
# [>] EXECUTING SESSION PATH RESOLUTION & PROVISIONING
def resolve_session_path(
    base_dir: str,
    current_session_path: str | None,
    force_new: bool,
    target_uid: int,
    target_gid: int,
    user_home: str,
) -> str:
    """
    Provisions secure physical storage and generates a timestamped session log.

    Args:
        base_dir (str): The base directory path for storing session logs (supports tilde expansion).
        current_session_path (str | None): The existing active session log path, if any.
        force_new (bool): Flag indicating whether a new session log should be forced.
        target_uid (int): The target User ID (UID) for setting file and directory ownership.
        target_gid (int): The target Group ID (GID) for setting file and directory ownership.
        user_home (str): The resolved home directory path of the human user.

    Returns:
        str: The absolute file path to the newly provisioned or existing session log.
    """
    # SESSION PATH EVALUATION & PROVISIONING TRIGGER
    # Checks whether a new session log needs to be provisioned (forced or missing current path).
    if force_new or not current_session_path:
        # BASE DIRECTORY PATH EXPANSION
        # Resolves tilde paths using the user's home directory or falls back to general expansion.
        resolved_base = (
            base_dir.replace("~", user_home, 1)
            if base_dir.startswith("~")
            else os.path.expanduser(base_dir)
        )

        # DIRECTORY CREATION & PRIVILEGE ADJUSTMENT
        # Creates the base directory structure and adjusts ownership if running with root privileges.
        os.makedirs(resolved_base, exist_ok=True)
        if os.geteuid() == 0:
            os.chown(resolved_base, target_uid, target_gid)

        # TIMESTAMPED LOG GENERATION & INITIALIZATION
        # Generates a unique microsecond-precision timestamped log filename, initializes the file,
        # and applies secure user/group ownership when running as root.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        session_file = os.path.join(resolved_base, f"session_{timestamp}.log")
        open(session_file, "a").close()

        if os.geteuid() == 0:
            os.chown(session_file, target_uid, target_gid)

        return session_file

    return current_session_path


# SYSTEM UTILITIES SUBSYSTEM: LOG ROTATION & RETENTION PURGING
# This utility manages log file lifecycle by purging historical session logs
# that exceed the configured maximum retention threshold in days.
# [>] EXECUTING LOG ROTATION & PURGING
def rotate_logs(session_path: str | None, max_log_days: int) -> None:
    """
    Purges log files older than the retention threshold.

    Args:
        session_path (str | None): The active session file path used to derive the target log directory.
        max_log_days (int): The maximum retention period in days before logs are purged.

    Returns:
        None
    """
    # PATH VALIDATION & DIRECTORY CHECK
    # Returns immediately if the session path is unassigned or the target log directory does not exist.
    if not session_path:
        return

    log_dir = os.path.dirname(session_path)
    if not os.path.exists(log_dir):
        return

    # RETENTION THRESHOLD CALCULATION
    # Converts the maximum retention days into seconds and captures the current epoch timestamp.
    seconds_threshold = max_log_days * 24 * 60 * 60
    current_time = time.time()

    # DIRECTORY SCAN & FILE PRUNING
    # Iterates through all files in the log directory, checking file modification times against the threshold
    # and safely removing expired logs.
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            if (current_time - os.path.getmtime(file_path)) > seconds_threshold:
                try:
                    os.remove(file_path)
                except Exception:
                    pass
