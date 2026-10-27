import os

from .symlink import verify_symlink_trust  # type: ignore[import-not-found]
from .permissions import verify_posix_ownership_and_permissions  # type: ignore[import-not-found]
from .acls import verify_acls  # type: ignore[import-not-found]
from .contants import report_status, log_path  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: HARDENED BINARY DISCOVERY & SECURITY AUDIT
# This utility iterates through trusted effective search scopes to locate, verify,
# and audit system binaries against symlink traversal, owner privileges, permissions, and hidden ACLs.
# [>] EXECUTING HARDENED BINARY SEARCH & VALIDATION
def find_hardened_binary(tool: str, effective_scopes: tuple[str, ...]) -> str | None:
    """
    Iterates through effective scopes to locate and audit a single binary.

    Args:
        tool (str): The filename of the target binary to locate.
        effective_scopes (tuple[str, ...]): A tuple of trusted directory scope paths to search.

    Returns:
        str | None: The path to the fully audited and verified binary, or None if no hardened binary is found.
    """
    # SCOPE ITERATION & PATH CONSTRUCTION
    # Iterates over each trusted scope directory to construct and inspect the candidate binary path.
    for directory in effective_scopes:
        test_path = os.path.normpath(os.path.join(directory, tool))

        # EXISTENCE & EXECUTABLE CHECK
        # Verifies that the candidate path exists on disk and has executable permissions.
        if os.path.exists(test_path) and os.access(test_path, os.X_OK):
            # SYMLINK & SCOPE TRUST AUDIT
            # Resolves symlinks and ensures the destination remains within trusted scopes.
            real_destination = verify_symlink_trust(test_path, effective_scopes)
            if not real_destination:
                report_status(
                    state="warn",
                    message=f"Security Warning: {test_path} (OUTSIDE SCOPE)",
                    log_path=log_path,
                )
                continue

            # POSIX OWNERSHIP & PERMISSION AUDIT
            # Validates root UID ownership and ensures the file is not writable by groups or others.
            if not verify_posix_ownership_and_permissions(real_destination):
                report_status(
                    state="warn",
                    message=f"Integrity Rejection: {real_destination} failed ownership check.",
                    log_path=log_path,
                )
                continue

            # EXTENDED ATTRIBUTE ACL INTEGRITY PROBE
            # Probes for hidden extended attribute ACLs that could bypass standard POSIX permissions.
            try:
                verify_acls(real_destination)
            except Exception as e:
                report_status(state="warn", message=str(e), log_path=log_path)
                continue

            # SUCCESSFUL VERIFICATION RETURN
            # Returns the verified test path once all security, ownership, and ACL checks pass.
            return test_path

    return None
