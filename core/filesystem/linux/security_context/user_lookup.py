import pwd
import sys


# USER METADATA FETCH & POSIX DATABASE QUERY ENGINE
# This utility queries the system password database to retrieve account metadata
# for a target username. By trapping missing user lookup failures, it ensures
# graceful error logging and controlled execution termination.
# [>] EXECUTING USER METADATA FETCH
def fetch_user_metadata(username: str) -> pwd.struct_passwd:
    """
    Queries the system pwd database to retrieve metadata for a given username.

    Args:
        username: The target username string to search.

    Returns:
        pwd.struct_passwd: System user account details.
    """
    # POSIX DATABASE QUERY INVOCATION
    # Attempts to look up the target username in the system password database.
    try:
        return pwd.getpwnam(username)
    except KeyError as e:
        # KEYERROR RECOVERY & TERMINAL EXIT
        # Handles missing user entries by writing a descriptive error message
        # directly to stderr and terminating execution.
        sys.stderr.write(f"[!] Critical Security Context Error: User not found: {e}\n")
        sys.exit(1)
