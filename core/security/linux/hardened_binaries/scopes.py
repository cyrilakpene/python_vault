from typing import Set

BASE_SCOPES: tuple[str, ...] = ("/usr/bin", "/bin", "/usr/sbin", "/sbin")


# DATA PROCESSING SUBSYSTEM: EFFECTIVE SCOPE CONSTRUCTION
# This utility constructs effective search and filter scopes by combining safe zone scopes
# with baseline scopes based on system locks and priority flags.
# [>] EXECUTING EFFECTIVE SCOPES CONSTRUCTION
def build_effective_scopes(
    safe_scopes: tuple[str, ...] | None, is_priority: bool
) -> tuple[str, ...]:
    """
    Constructs effective search scopes based on system locks and priority flags.

    Args:
        safe_scopes (tuple[str, ...] | None): An optional tuple of safe zone scope strings.
        is_priority (bool): Flag indicating whether safe scopes take priority and should be evaluated first.

    Returns:
        tuple[str, ...]: The combined tuple of effective search scopes.
    """
    # PRIORITY SCOPE EVALUATION & COMBINATION
    # If safe scopes are provided and priority is enabled, prepends safe scopes to baseline scopes;
    # otherwise, appends safe scopes (or an empty tuple) to baseline scopes.
    if safe_scopes and is_priority:
        return safe_scopes + BASE_SCOPES

    return BASE_SCOPES + (safe_scopes or ())


# DATA PROCESSING SUBSYSTEM: PRIORITY TARGET SET NORMALIZATION
# This utility normalizes a collection of priority target strings into an uppercase,
# case-insensitive lookup set for fast-path filtering and matching.
# [>] EXECUTING PRIORITY TARGET SET NORMALIZATION
def build_priority_set(priority_targets: list[str] | None) -> Set[str]:
    """
    Normalizes priority targets into a case-insensitive lookup set.

    Args:
        priority_targets (list[str] | None): An optional list of priority target strings.

    Returns:
        Set[str]: A set of uppercase priority target strings for case-insensitive matching; empty set if None.
    """
    # PRIORITY TARGET NORMALIZATION & SET COMPREHENSION
    # Iterates through priority targets if provided, converting each string to uppercase
    # to construct a high-performance lookup set, returning an empty set otherwise.
    return {t.upper() for t in priority_targets} if priority_targets else set()
