import sys


# SYSTEM PATH INJECTION & IDEMPOTENT RESOLUTION ENGINE
# This utility ensures target directories are prioritized at the head of Python's module search path.
# By performing idempotent checks against sys.path[0], it prevents duplicate entries while
# guaranteeing immediate module import precedence for synthesis or runtime execution.
# [>] EXECUTING SYSTEM PATH INJECTION
def inject_path(target_path: str) -> None:
    """
    Checks the leading index of sys.path and injects the target path idempotently.

    Args:
        target_path: The file system directory path string to inject into Python's search path.
    """
    # SYS.PATH PRECEDENCE CHECK & IDEMPOTENT INSERTION
    # Verifies whether the target path already occupies the primary index (sys.path[0]).
    # If not, inserts it cleanly at the head of the list to guarantee highest import priority.
    if sys.path[0] != target_path:
        sys.path.insert(0, target_path)
