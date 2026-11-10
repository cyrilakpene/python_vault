import pwd
import sys

from .identity_resolver import resolve_invoking_user  # type: ignore[import-not-found]
from .privilege_gate import SudoMode, enforce_privilege_policy  # type: ignore[import-not-found]
from .user_lookup import fetch_user_metadata  # type: ignore[import-not-found]


# SECURITY CONTEXT INITIALIZATION & ORCHESTRATION ENGINE
# This utility orchestrates the security verification pipeline by sequentially enforcing
# execution privilege rules, resolving the invoking user identity, and retrieving
# system account metadata, while cleanly handling runtime exceptions.
# [>] EXECUTING SECURITY CONTEXT INITIALIZATION
def initialize_security_context(
    sudo_mode: SudoMode = "forbid",
) -> tuple[str, pwd.struct_passwd]:
    """Initializes and verifies the process execution context.

    Args:
        sudo_mode: Execution mode rule ("require", "forbid", or "allow").

    Returns:
        tuple[str, pwd.struct_passwd]: (ORIGINAL_USER, USER_INFO) containing
        the username and its pwd structure metadata.
    """
    try:
        # PRIVILEGE POLICY ENFORCEMENT
        # Evaluates process execution rights against the configured sudo mode rule.
        # [>] ENFORCING PRIVILEGE POLICY
        enforce_privilege_policy(sudo_mode)

        # INVOKING USER IDENTIFICATION
        # Resolves the true user invoking the process via environment and database fallbacks.
        # [>] RESOLVING INVOKING USER
        original_user = resolve_invoking_user()

        # SYSTEM METADATA ACQUISITION
        # Queries the POSIX password database to retrieve account details for the user.
        # [>] FETCHING SYSTEM METADATA
        user_info = fetch_user_metadata(original_user)

        # CONTEXT MANIFEST RETURN
        # Returns the validated username and its corresponding password database structure.
        return original_user, user_info

    except SystemExit:
        # SYSTEM EXIT PASS-THROUGH
        # Cleanly re-raises explicit termination requests originating from privilege or lookup gates.
        raise
    except Exception as e:
        # UNEXPECTED ERROR TRAP & TERMINATION
        # Catches unforeseen low-level execution exceptions, writes to stderr, and exits.
        sys.stderr.write(f"[!] Unexpected error during initialization: {e}\n")
        sys.exit(1)
