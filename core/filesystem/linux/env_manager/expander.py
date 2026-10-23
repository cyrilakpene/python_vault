import os


# PATH EXPANSION & TILDE RESOLUTION ENGINE
# This utility expands tilde (~) home directory shortcuts across production and development paths.
# By safely handling optional target inputs and leveraging operating system user expansion rules,
# it ensures accurate and reliable file system path resolution.
# [>] EXECUTING PATH EXPANSION & RESOLUTION
def expand_paths(prod_path: str, dev_path: str | None = None) -> tuple[str, str | None]:
    """
    Expands tilde (~) shortcuts across both potential target paths.

    Args:
        prod_path: The primary production file system path string requiring tilde expansion.
        dev_path: Optional secondary development file system path string.

    Returns:
        tuple[str, str | None]: A tuple containing the expanded production path and the optionally expanded development path.
    """
    # DEV PATH CONDITIONAL EXPANSION
    # Checks if a development path is provided, expanding its tilde shortcut if present;
    # otherwise, preserves the None default value.
    expanded_dev = os.path.expanduser(dev_path) if dev_path else None

    # PRODUCTION PATH EXPANSION
    # Unconditionally expands tilde shortcuts in the primary production path string.
    expanded_prod = os.path.expanduser(prod_path)

    # PATH MANIFEST RETURN
    # Returns the fully resolved path tuple for downstream file operations.
    return expanded_prod, expanded_dev
