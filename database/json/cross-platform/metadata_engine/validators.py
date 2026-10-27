from typing import Any


# DATA CONTAINER SUBSYSTEM: CONFIGURATION VALIDATION & SAFE ZONE GUARD
# This utility ensures safe zone configuration parameters are explicitly declared and validated
# when null stripping operations are enabled within the data processing library.
# [>] EXECUTING CONFIGURATION VALIDATION
def validate_configuration(strip_null: bool, scope: str | list[str] | None) -> None:
    """
    Ensures safe zone configuration is explicitly declared if null stripping is enabled.

    Args:
        strip_null (bool): Flag indicating whether null values should be stripped during processing.
        scope (str | list[str] | None): The target scope or collection of paths representing the safe zone.

    Raises:
        ValueError: If strip_null is True but scope is not defined (None).
    """
    # NULL STRIPPING & SCOPE VERIFICATION
    # Validates that a safe zone scope is explicitly defined when null stripping is active,
    # raising a ValueError with usage instructions if omitted.
    if strip_null and scope is None:
        raise ValueError(
            "Configuration Error: 'scope' must be defined when 'strip_null' is True. "
            "Pass a string or a list of strings (e.g., ['general', '.'])."
        )


# DATA CONTAINER SUBSYSTEM: SOURCE SIGNATURE VERIFICATION & INTEGRITY FIREWALL
# This utility validates that all expected data sources contain their mandatory signature keys,
# raising a KeyError if an integrity failure or missing signature is detected.
# [>] EXECUTING SOURCE SIGNATURE VERIFICATION
def verify_source_signatures(
    sources: dict[str, Any], signatures: dict[str, str]
) -> None:
    """
    Validates that all expected data sources contain their mandatory signature keys.

    Args:
        sources (dict[str, Any]): A dictionary mapping source aliases to their respective data containers.
        signatures (dict[str, str]): A dictionary mapping source aliases to their mandatory signature keys.

    Raises:
        KeyError: If any source is missing its designated mandatory signature key.
    """
    # SIGNATURE MAPPING ITERATION & INTEGRITY CHECK
    # Iterates through each source alias and its expected signature key,
    # verifying presence within the respective source content and raising a KeyError on failure.
    for alias, sig_key in signatures.items():
        source_content: dict[str, Any] = sources.get(alias, {})
        if sig_key not in source_content:
            raise KeyError(
                f"Integrity Failure: Source '{alias}' is missing "
                f"the mandatory signature key: '{sig_key}'."
            )


# DATA CONTAINER SUBSYSTEM: TARGET OVERLAP DETECTION & MAPPING COLLISION FIREWALL
# This utility prevents mapping collisions by ensuring a target leaf path isn't populated twice,
# raising a ValueError if duplicate target assignment occurs and overlap is disallowed.
# [>] EXECUTING TARGET OVERLAP VERIFICATION
def check_target_overlap(
    target_path: str, assigned_targets: set[str], allow_target_overlap: bool
) -> None:
    """
    Prevents mapping collisions by ensuring a target leaf isn't populated twice.

    Args:
        target_path (str): The target destination leaf path being evaluated.
        assigned_targets (set[str]): A running set tracking already-assigned target paths.
        allow_target_overlap (bool): Flag indicating whether multiple source paths can populate the same target leaf.

    Raises:
        ValueError: If overlap is disallowed and the target path already exists in assigned_targets.
    """
    # OVERLAP VERIFICATION & COLLISION GUARD
    # Checks if target overlap is disallowed and whether the target path has already been assigned.
    # Raises a ValueError if a mapping collision is detected.
    if not allow_target_overlap and target_path in assigned_targets:
        raise ValueError(
            f"Target Collision: Multiple source paths are attempting to "
            f"populate the same target leaf: '{target_path}'."
        )

    # TARGET REGISTRATION
    # Adds the validated target path to the set of assigned targets for future collision checks.
    assigned_targets.add(target_path)
