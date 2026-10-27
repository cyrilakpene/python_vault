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
