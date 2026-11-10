import os
import sys
from typing import Literal

# SUDO MODE POLICY DEFINITION TYPE
# This type alias defines the allowed execution mode rules for privilege enforcement,
# supporting mandatory root execution, explicit prohibition, or permissive bypass.
SudoMode = Literal["require", "forbid", "allow"]


# PRIVILEGE POLICY ENFORCEMENT ENGINE
# This utility evaluates the process effective user ID against the configured
# sudo mode policy, enforcing administrative boundaries and terminating execution
# if the security context rules are violated.
# [>] EXECUTING PRIVILEGE POLICY ENFORCEMENT
def enforce_privilege_policy(sudo_mode: SudoMode) -> None:
    """
    Evaluates the process effective user ID against the configured sudo mode policy.

    Args:
        sudo_mode: Execution mode rule ("require", "forbid", or "allow").
    """
    # EFFECTIVE USER ID RESOLUTION
    # Determines whether the current process is running with root privileges.
    is_root = os.geteuid() == 0

    # REQUIRE PRIVILEGE GATE EVALUATION
    # Checks if root execution is mandatory under the current policy,
    # writing an error and terminating if privileges are insufficient.
    if sudo_mode == "require" and not is_root:
        sys.stderr.write(
            "[!] Access Denied: This script must be executed as root or with 'sudo'.\n"
        )
        sys.exit(1)

    # FORBID PRIVILEGE GATE EVALUATION
    # Checks if root execution is strictly prohibited under the current policy,
    # writing an error and terminating if running as root.
    if sudo_mode == "forbid" and is_root:
        sys.stderr.write(
            "[!] Access Denied: This script must NOT be executed as root or with 'sudo'.\n"
        )
        sys.exit(1)
