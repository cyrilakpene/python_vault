import os
import stat


# SYSTEM UTILITIES SUBSYSTEM: POSIX OWNERSHIP & PERMISSIONS VERIFICATION
# This utility audits file system permissions and POSIX ownership, ensuring that sensitive
# files are owned by root and protected against write access by groups or others.
# [>] EXECUTING POSIX OWNERSHIP & PERMISSIONS AUDIT
def verify_posix_ownership_and_permissions(real_destination: str) -> bool:
    """
    Verifies root UID ownership and absence of group/others write permissions.

    Args:
        real_destination (str): The absolute physical file path to inspect.

    Returns:
        bool: True if the file is root-owned and not writable by group/others; False otherwise.
    """
    # FILE STATUS RETRIEVAL
    # Retrieves file system metadata via os.stat for permission and ownership inspection.
    file_info = os.stat(real_destination)

    # OWNERSHIP & PERMISSION FLAG EVALUATION
    # Checks whether the file UID is 0 (root) and verifies that group or world write bits are disabled.
    is_root_owned = file_info.st_uid == 0
    is_writable_by_others = bool(file_info.st_mode & (stat.S_IWGRP | stat.S_IWOTH))

    # COMPLIANCE CHECK
    # Returns True only if both root ownership and secure permission constraints are satisfied.
    return is_root_owned and not is_writable_by_others
