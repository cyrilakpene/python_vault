import os
import pwd


# INVOKING USER RESOLUTION ENGINE
# This utility identifies the original invoking user by cascading through
# environmental metadata and falling back to active POSIX user database queries.
# [>] EXECUTING INVOKING USER RESOLUTION
def resolve_invoking_user() -> str:
    """
    Resolves the original invoking user identity using environment variables
    and POSIX database fallbacks.

    Returns:
        str: The resolved username.
    """
    # ENVIRONMENT CASCADE & POSIX FALLBACK EVALUATION
    # Evaluates sudo execution metadata and standard user environment variables,
    # falling back to querying the system user ID database if necessary.
    return (
        os.environ.get("SUDO_USER")
        or os.environ.get("USER")
        or pwd.getpwuid(os.getuid()).pw_name
    )
