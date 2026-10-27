import os


# SYSTEM UTILITIES SUBSYSTEM: SYMLINK TRUST VERIFICATION & PATH SECURITY
# This utility resolves symbolic links and ensures that their physical destination
# remains securely within trusted file system scopes to prevent path traversal vulnerabilities.
# [>] EXECUTING SYMLINK TRUST VERIFICATION
def verify_symlink_trust(
    test_path: str, effective_scopes: tuple[str, ...]
) -> str | None:
    """
    Resolves symlinks and ensures physical destination stays within trusted scopes.

    Args:
        test_path (str): The file system path containing the potential symbolic link.
        effective_scopes (tuple[str, ...]): A tuple of trusted directory scope paths.

    Returns:
        str | None: The fully resolved real path if trusted; None if the destination escapes trusted scopes.
    """
    # REAL PATH RESOLUTION
    # Resolves any symbolic links in the test path to determine its ultimate physical destination on disk.
    real_destination = os.path.realpath(test_path)

    # SCOPE TRUST VALIDATION
    # Checks whether the real physical destination starts with any of the approved effective scope paths.
    is_trusted_origin = any(
        real_destination.startswith(scope) for scope in effective_scopes
    )

    # CONDITIONAL RETURN
    # Returns the real destination path if trusted, or None to reject untrusted symlink targets.
    return real_destination if is_trusted_origin else None
