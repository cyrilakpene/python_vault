import sys
import os
import pwd
from typing import Literal


# SECURITY CONTEXT RESOLUTION PIPELINE
# This module implements an execution context verification and privilege gate.
# By checking real user IDs and resolving invoking sudo identities, we ensure
# that administrative tasks run with valid credentials without dropping critical
# user context required for logging or permission assignments.
SudoMode = Literal["require", "forbid", "allow"]


def initialize_security_context(
    sudo_mode: SudoMode = "forbid",
) -> tuple[str, pwd.struct_passwd]:
    """Initializes and verifies execution context.

    This engine bridges the gap between root privilege escalation and user
    identity tracking by validating process execution states. The identity
    resolution sequence is governed by system privileges, environment
    variables, and POSIX user databases.

    Args:
        sudo_mode: Execution mode rule: - "require": Exits if the script is NOT
          run as root/sudo. - "forbid": Exits if the script IS run as root/sudo.
          - "allow": Bypasses privilege gates and executes regardless of root
          state.

    Returns:
        tuple: (ORIGINAL_USER, USER_INFO) containing the username and pwd
        structure.
    """
    try:
        # PRIVILEGE GATE: ROOT POLICING RESOLUTION
        # We evaluate the effective user ID (EUID) against configured administrative rules.
        # If execution privileges violate the target mode, we issue an immediate exit.
        # [>] EVALUATING PRIVILEGE STATE
        is_root = os.geteuid() == 0

        if sudo_mode == "require" and not is_root:
            # TERMINAL EXIT: PRIVILEGE ESCALATION REQUIRED
            # We emit an explicit access rejection message directly to stderr.
            sys.stderr.write(
                "[!] Access Denied: This script must be executed as root or with"
                " 'sudo'.\n"
            )
            sys.exit(1)

        if sudo_mode == "forbid" and is_root:
            # TERMINAL EXIT: ELEVATED PRIVILEGES FORBIDDEN
            # We reject execution to prevent unintended file ownership mutations or operations.
            sys.stderr.write(
                "[!] Access Denied: This script must NOT be executed as root or"
                " with 'sudo'.\n"
            )
            sys.exit(1)

        # IDENTITY RESOLUTION PIPELINE: INVOKING USER IDENTIFICATION
        # We query system environment variables to identify the original invoking user.
        # Fallbacks cascade from sudo metadata to active user state and passwd resolution.
        # [>] RESOLVING INVOKING USER
        original_user = (
            os.environ.get("SUDO_USER")
            or os.environ.get("USER")
            or pwd.getpwuid(os.getuid()).pw_name
        )

        # POSIX STRUCT LOOKUP: USER DATABASE QUERY
        # We query the pwd database to acquire system metadata for the target identity.
        # [>] FETCHING USER METADATA
        user_info = pwd.getpwnam(original_user)

        return original_user, user_info

    except KeyError as e:
        # DEFENSIVE GATE: UNKNOWN USER RESOLUTION FAILURE
        # Handles instances where the resolved username lacks an entry in the pwd database.
        # [>] EXECUTING KEYERROR RECOVERY
        sys.stderr.write(f"[!] Critical Security Context Error: User not found: {e}\n")
        sys.exit(1)
    except Exception as e:
        # DEFENSIVE GATE: UNHANDLED EXCEPTION CATCH-ALL
        # Catches unexpected low-level operational failures during context initialization.
        # [>] EXECUTING CRITICAL FAILURE ROUTINE
        sys.stderr.write(f"[!] Unexpected error during initialization: {e}\n")
        sys.exit(1)

