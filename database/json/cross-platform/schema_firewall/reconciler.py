from typing import Any

from .constants import report_status, log_path, get_deep_value  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: SCHEMA VALIDATION & FIELD SATISFACTION ENGINE
# This utility verifies whether an individual schema field requirement is satisfied within existing data,
# supporting direct root-level matching and advanced path traversal via mapping dictionaries.
# [>] EXECUTING FIELD SATISFACTION CHECK
def is_field_satisfied(
    field: dict[str, Any],
    existing_data: dict[str, Any],
    mapping: dict[str, str] | None = None,
) -> bool:
    """
    Checks if a single schema field is satisfied via direct match or mapped path traversal.

    Args:
        field (dict[str, Any]): The schema field definition containing the target key.
        existing_data (dict[str, Any]): The existing data container or pool to validate against.
        mapping (dict[str, str] | None, optional): Optional field-to-path mapping dictionary. Defaults to None.

    Returns:
        bool: True if the field is satisfied via direct match or resolved path; False otherwise.
    """
    # SCHEMA KEY EXTRACTION & VALIDATION
    # Retrieves the required key from the field definition, reporting a warning and returning False
    # if the schema entry is malformed or missing a key.
    schema_key: str | None = field.get("key")
    if not schema_key:
        report_status(
            state="warn",
            message="Invalid schema entry detected (missing key).",
            log_path=log_path,
            silent=True,
        )
        return False

    # DIRECT ROOT-LEVEL MATCH CHECK
    # Checks if the schema key exists directly at the root level of the existing data dictionary,
    # logging an informational match and returning True if found.
    if schema_key in existing_data:
        report_status(
            state="item",
            message=f"Match found: Root-level key {schema_key!r} exists.",
            log_path=log_path,
            silent=True,
        )
        return True

    # MAPPED PATH RESOLUTION & DEEP VALUE LOOKUP
    # Checks if an alternative mapping exists for the schema key, resolving the target path
    # within the existing data structure via deep value lookup.
    if mapping and schema_key in mapping:
        db_path: str = mapping[schema_key]
        report_status(
            state="info",
            message=f"Resolving mapped path: {schema_key!r} -> {db_path!r}.",
            log_path=log_path,
            silent=True,
        )

        resolved_val = get_deep_value(existing_data, db_path)
        if resolved_val is not None:
            report_status(
                state="item",
                message=f"Match found: Path {db_path!r} resolved to value.",
                log_path=log_path,
                silent=True,
            )
            return True

    # UNSATISFIED FIELD FALLBACK
    # Returns False if neither root-level key nor mapped path resolution yields a valid value.
    return False
