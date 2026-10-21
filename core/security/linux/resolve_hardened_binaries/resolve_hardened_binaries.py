import os
import stat

from report_status import report_status  # type: ignore[import-not-found]


# EXTENDED ACCESS CONTROL (ACL) INTEGRITY PROBE EXCEPTION
# Custom exception domain class used to signal when an extended attribute ACL verification fails or encounters an OS error.
# Standardizes security audit failure formatting across file operations to enforce Zero-Trust fallback policies.
class ACLProbeError(Exception):
    """Raised when an extended attribute ACL integrity probe fails."""

    def __init__(
        self,
        path: str,
        message: str = "Could not verify extended attributes.",
        fallback_unsafe: bool = True,
    ):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes audit failure message with standard security tag, path details, and fallback status before delegating to BaseException initializer.
        super().__init__(
            f"ACL audit failure: {message} Path: {path} (Zero-Trust Fallback Unsafe: {fallback_unsafe})"
        )
        self.path = path
        self.fallback_unsafe = fallback_unsafe


# SECURITY CIRCUIT BREAKER EXCEPTION
# Custom exception domain class used to signal when mandatory system binaries or dependencies fail verification.
# Standardizes security failure formatting across CLI workflows to gracefully halt execution instead of hard exiting.
class SecurityCircuitBreakerError(Exception):
    """Raised when mandatory security dependencies or binaries are missing or untrusted."""

    def __init__(
        self,
        missing_tools: list[str],
        message: str = "Missing or untrusted binaries.",
    ):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes security failure message with standard tag, missing tools list, and details before delegating to BaseException initializer.
        tools_str = ", ".join(missing_tools)
        super().__init__(f"Security failure: {message} [{tools_str}]")
        self.missing_tools = missing_tools


# ARCHITECTURAL GATEKEEPER: ZERO-TRUST BINARY RESOLUTION
# This engine implements a "Verify-then-Trust" protocol for system executables.
# By bypassing the user-defined $PATH and enforcing strict POSIX ownership,
# root-only write bits, and ACL-free status, it neutralizes common Kali Linux
# attack vectors such as Binary Planting and Symlink redirection.
def resolve_hardened_binaries(
    tools: list[str],
    safe_scopes: tuple[str, ...] | None = None,
    prioritize_custom: bool = False,
    priority_targets: list[str] | None = None,
) -> dict[str, str]:
    """Locates and validates system binaries by bypassing environment variables ($PATH), ensuring the pipeline only interacts with trusted, root-owned executables.

    Args:
        tools: List of binary tool names to resolve and validate.
        safe_scopes: Optional tuple of custom directory paths to include in the search scope.
        prioritize_custom: If True, moves custom scope paths to the front of the search order.
        priority_targets: Optional list of specific binary targets that receive custom-first priority.

    Returns:
        A dictionary mapping uppercase tool names to their validated absolute filesystem paths.
    """

    # SYSTEM-LEVEL IMMUTABLE SCOPES
    # Hardened OS sources of truth, bypassing user-defined $PATH variables.
    BASE_SCOPES: tuple[str, ...] = ("/usr/bin", "/bin", "/usr/sbin", "/sbin")

    # REGISTRY & DEFICIT TRACKING
    # Initializes tracking for resolved binary paths and missing critical dependencies.
    resolved_registry: dict[str, str] = {}
    missing_tools: list[str] = []

    # PRE-PROCESS AUTHORIZATION WHITELIST
    # Normalizes priority targets into a Set for efficient case-insensitive lookups.
    priority_set: set[str] = (
        {t.upper() for t in priority_targets} if priority_targets else set()
    )

    for tool in tools:
        found_path: str | None = None
        current_tool_upper: str = tool.upper()

        # DYNAMIC SEARCH PRECEDENCE LOGIC
        # Determines if custom scopes take priority based on global flags or surgical lists.
        is_priority: bool = prioritize_custom or current_tool_upper in priority_set

        # SCOPE PRECEDENCE & SHADOWING CONTROL
        # Constructs effective search scopes, enforcing system-lock safety by default.
        if safe_scopes and is_priority:
            effective_scopes: tuple[str, ...] = (
                safe_scopes + BASE_SCOPES
            )  # Custom first
        else:
            effective_scopes = BASE_SCOPES + (safe_scopes or ())  # System lock first

        for directory in effective_scopes:
            # PATH NORMALIZATION & TRAVERSAL DEFENSE
            # Collapses relative sequences to evaluate clean, absolute target paths.
            test_path: str = os.path.normpath(os.path.join(directory, tool))

            # ACCESSIBILITY & EXECUTION GATE
            # Verifies physical existence and executable permissions on the target path.
            if os.path.exists(test_path) and os.access(test_path, os.X_OK):

                # CHAIN-OF-TRUST (SYMLINK INTEGRITY AUDIT)
                # Resolves symlinks to their actual physical disk destination.
                real_destination: str = os.path.realpath(test_path)

                # SCOPE BOUNDARY ENFORCEMENT
                # Ensures the resolved physical destination remains within authorized scopes.
                is_trusted_origin: bool = any(
                    real_destination.startswith(scope) for scope in effective_scopes
                )

                if not is_trusted_origin:
                    report_status(
                        state="warn",
                        message=f"Security Warning: {test_path} -> {real_destination} (OUTSIDE SCOPE)",
                    )
                    continue

                # POSIX OWNERSHIP & BITMASK INTEGRITY AUDIT
                # Verifies that binaries are root-owned and lack group/others write permissions.
                file_info: os.stat_result = os.stat(real_destination)
                is_root_owned: bool = file_info.st_uid == 0  # Gate 1: Root UID

                # Check for Group-Writable (S_IWGRP) or Others-Writable (S_IWOTH).
                is_writable_by_others: int = file_info.st_mode & (
                    stat.S_IWGRP | stat.S_IWOTH
                )  # Gate 2: Bitmask check

                if not is_root_owned or is_writable_by_others:
                    reason: str = (
                        "NOT ROOT-OWNED" if not is_root_owned else "WORLD-WRITABLE"
                    )
                    report_status(
                        state="warn",
                        message=f"Integrity Rejection: {real_destination} is {reason}.",
                    )
                    continue

                # EXTENDED ACCESS CONTROL (ACL) INTEGRITY PROBE
                # Probes for hidden extended attribute access controls that could bypass POSIX permissions.
                try:
                    has_acl: bool = "system.posix_acl_access" in os.listxattr(
                        real_destination
                    )
                except OSError as e:
                    has_acl = True
                    raise ACLProbeError(
                        path=real_destination,
                        message=f"Could not verify xattrs due to OS error: {e}",
                    )

                if has_acl:
                    report_status(
                        state="warn",
                        message=f"Security Alert: {real_destination} has hidden ACLs.",
                    )
                    continue

                found_path = test_path
                break

        # SUCCESSFUL RESOLUTION OR FAILURE TRACKING
        # Maps validated paths to uppercase registry keys or registers missing dependencies.
        if found_path:
            resolved_registry[current_tool_upper] = found_path
        else:
            missing_tools.append(tool)

    # SECURITY CIRCUIT BREAKER (TERMINATION LOGIC)
    # Halts execution and raises an exception if any mandatory dependency fails verification.
    if missing_tools:
        raise SecurityCircuitBreakerError(missing_tools=missing_tools)

    return resolved_registry
