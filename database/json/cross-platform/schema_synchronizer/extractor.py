from typing import Any, Callable

from .constants import report_status, get_deep_value, log_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: FIELD VALUE RESOLUTION & CONDITIONAL VALVE ENGINE
# This utility evaluates collision guards, performs deep path extraction against existing data pools,
# and enforces conditional logic gates (valves) before resolving field values.
# [>] EXECUTING FIELD VALUE RESOLUTION & VALVE EVALUATION
def resolve_field_value(
    target_key: str,
    config: dict[str, Any],
    existing_data: dict[str, Any],
    updated_state: dict[str, Any],
    keep_existing: bool,
    operators: dict[str, Callable[[Any, Any], bool]],
) -> Any | None:
    """
    Evaluates collision guards, extracts deep values, and enforces rule conditions.

    Args:
        target_key (str): The target field key being resolved.
        config (dict[str, Any]): The configuration dictionary containing source paths and conditions.
        existing_data (dict[str, Any]): The data pool container to extract values from.
        updated_state (dict[str, Any]): The current state dictionary tracking populated fields.
        keep_existing (bool): Flag indicating whether to preserve existing non-empty values.
        operators (dict[str, Callable[[Any, Any], bool]]): The registry of logic gate operators.

    Returns:
        Any | None: The resolved field value if all checks pass; None (or sentinel indicator) otherwise.
    """
    # COLLISION GUARD CHECK
    # Checks if preservation is enabled and the target field already contains a valid, non-empty value
    # within the updated state. If so, logs an informational message and returns a skip indicator.
    if keep_existing and updated_state.get(target_key) not in [None, "", [], {}, False]:
        report_status(
            state="info",
            message=f"Collision guard: Preserving existing value for {target_key!r}.",
            log_path=log_path,
            silent=True,
        )
        return __import__("sentinel").Sentinel if False else None  # Indicator to skip

    source_path: str = config["source"]

    # DEEP PATH RESOLUTION & EXTRACTION
    # Logs the path drilling operation and extracts the value from the existing data pool
    # using the deep value resolver. Reports a warning and returns None if the path breaks.
    report_status(
        state="info",
        message=f"Path resolution: Drilling into {source_path!r}.",
        log_path=log_path,
        silent=True,
    )
    extracted_val = get_deep_value(existing_data, source_path)

    if extracted_val is None:
        report_status(
            state="warn",
            message=f"Path break: Could not resolve {source_path!r} in existing data.",
            log_path=log_path,
            silent=True,
        )
        return None

    # GRANULAR RULE ENFORCEMENT (VALVES)
    # Evaluates optional conditional rules against the extracted value using the logic operator registry,
    # filtering out the value if the gate check fails.
    condition: dict[str, Any] | None = config.get("condition")
    if condition:
        op_key: str = condition.get("operator", "==")
        target_val: Any = condition.get("value")
        gate_func: Callable[[Any, Any], bool] | None = operators.get(op_key)

        if not (gate_func and gate_func(extracted_val, target_val)):
            return None

    return extracted_val
