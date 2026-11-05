import os

from .exceptions import ACLProbeError# type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: EXTENDED ATTRIBUTE ACL VERIFICATION
# This utility probes for hidden POSIX Access Control Lists (ACLs) stored in extended attributes
# that could potentially bypass standard POSIX file permissions.
# [>] EXECUTING EXTENDED ATTRIBUTE ACL PROBE
def verify_acls(real_destination: str) -> None:
    """
    Probes for hidden extended attribute ACLs that could bypass POSIX permissions.

    Args:
        real_destination (str): The absolute physical file path to inspect for extended attributes.

    Returns:
        None

    Raises:
        ACLProbeError: If hidden ACLs are detected or if an OS error prevents extended attribute verification.
    """
    # EXTENDED ATTRIBUTE INSPECTION & ACL PROBE
    # Attempts to list extended attributes on the target path and checks for the presence
    # of system POSIX ACL access attributes that could override standard permission bits.
    try:
        if "system.posix_acl_access" in os.listxattr(real_destination):
            raise ACLProbeError(path=real_destination, message="Hidden ACLs detected.")
    except OSError as e:
        # OS ERROR HANDLING & EXCEPTION ESCALATION
        # Catches file system errors during xattr probing and wraps them in an ACLProbeError.
        raise ACLProbeError(
            path=real_destination,
            message=f"Could not verify xattrs due to OS error: {e}",
        )
