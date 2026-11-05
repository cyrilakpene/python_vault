from .scopes import build_effective_scopes, build_priority_set  # type: ignore[import-not-found]
from .traversal import find_hardened_binary  # type: ignore[import-not-found]
from .exceptions import SecurityCircuitBreakerError  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: ZERO-TRUST BINARY RESOLUTION PIPELINE
# This utility orchestrates the zero-trust binary resolution and security audit pipeline
# across micro-modules, building lookup registries and enforcing strict circuit breakers for missing tools.
# [>] EXECUTING ZERO-TRUST BINARY RESOLUTION
def resolve_hardened_binaries(
    tools: list[str],
    safe_scopes: tuple[str, ...] | None = None,
    prioritize_custom: bool = False,
    priority_targets: list[str] | None = None,
) -> dict[str, str]:
    """
    Orchestrates the zero-trust binary resolution pipeline across micro-modules.

    Args:
        tools (list[str]): A list of binary tool names to resolve and audit.
        safe_scopes (tuple[str, ...] | None, optional): Optional tuple of trusted search scope paths. Defaults to None.
        prioritize_custom (bool, optional): Flag indicating whether to prioritize custom scopes. Defaults to False.
        priority_targets (list[str] | None, optional): Optional list of specific tools requiring priority resolution. Defaults to None.

    Returns:
        dict[str, str]: A verified registry mapping uppercase tool names to their hardened absolute file paths.

    Raises:
        SecurityCircuitBreakerError: If any requested tool fails resolution or security verification.
    """
    # REGISTRY INITIALIZATION & PRIORITY PREPARATION
    # Initializes the resolved binary dictionary, the missing tools tracker,
    # and builds the uppercase priority target lookup set.
    resolved_registry: dict[str, str] = {}
    missing_tools: list[str] = []
    priority_set = build_priority_set(priority_targets)

    # TOOL RESOLUTION ITERATION & SCOPE BUILDING
    # Iterates through each target tool, evaluating priority status and constructing effective search scopes
    # before invoking the hardened binary finder.
    for tool in tools:
        current_tool_upper = tool.upper()
        is_priority = prioritize_custom or current_tool_upper in priority_set
        effective_scopes = build_effective_scopes(safe_scopes, is_priority)

        found_path = find_hardened_binary(tool, effective_scopes)

        if found_path:
            resolved_registry[current_tool_upper] = found_path
        else:
            missing_tools.append(tool)

    # CIRCUIT BREAKER VALIDATION
    # Raises a SecurityCircuitBreakerError if any required tool could not be resolved or verified.
    if missing_tools:
        raise SecurityCircuitBreakerError(missing_tools=missing_tools)

    # COMPLETION REPORTING & REGISTRY RETURN
    # Reports successful verification completion and returns the verified binary registry.
    report_status(
        state="done",
        message=f"Registry Emission Complete: {len(resolved_registry)} tools verified.",
        context=LogContext(
            component="security.hardened_binaries",
            log_path=log_path,
            silent=True,
            trace_id="hardened_binaries",
            actor=context.get("user"),
            payload={"verified_count": len(resolved_registry), "tools": tools},
        ),
    )
    return resolved_registry
