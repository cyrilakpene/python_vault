import os


# PATH RESOLUTION & FILESYSTEM VERIFICATION ENGINE
# This utility verifies file system path existence to select between development
# and production targets. By prioritizing local development overrides if present,
# it ensures correct configuration path fallback behavior.
# [>] EXECUTING TARGET PATH RESOLUTION
def resolve_target_path(expanded_prod: str, expanded_dev: str | None) -> str:
    """
    Verifies filesystem existence and selects the development or production path.

    Args:
        expanded_prod: The primary production file system path string.
        expanded_dev: Optional secondary development file system path string.

    Returns:
        str: The resolved file system path string (prioritizing existing dev paths over production).
    """
    # DEVELOPMENT PATH PRIORITY CHECK
    # Checks if a development path was provided and verified to exist on the filesystem,
    # returning it immediately if found.
    if expanded_dev and os.path.exists(expanded_dev):
        return expanded_dev

    # PRODUCTION PATH FALLBACK
    # Defaults to the production path if no valid development override exists.
    return expanded_prod
