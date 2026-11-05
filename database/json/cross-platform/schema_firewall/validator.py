from typing import Any

from .reconciler import is_field_satisfied  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: SCHEMA DELTA FILTER & REDUNDANCY FIREWALL
# This utility filters input schema definitions by evaluating field satisfaction against existing data,
# subtracting already-collected keys to prevent redundant data entry prompts.
# [>] EXECUTING SCHEMA DELTA FILTERING
def filter_schema_by_keys(
    input_schema: list[dict[str, Any]],
    existing_data: dict[str, Any],
    mapping: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Subtracts already-collected keys from a target schema to prevent redundant data entry.

    Args:
        input_schema (list[dict[str, Any]]): The full list of schema field definitions to evaluate.
        existing_data (dict[str, Any]): The existing data container or pool to validate against.
        mapping (dict[str, str] | None, optional): Optional field-to-path mapping dictionary. Defaults to None.

    Returns:
        list[dict[str, Any]]: A filtered schema containing only unsatisfied or missing fields.
    """
    # SATISFACTION REGISTRY INITIALIZATION
    # Reports the initialization of the validation registry and initializes a tracking set
    # for captured keys.
    report_status(
        state="task",
        message="Initializing schema satisfaction validation registry.",
        context=LogContext(
            component="database.filter_schema_by_keys",
            log_path=log_path,
            silent=True,
            trace_id="filter_schema_by_keys",
            actor=context.get("user"),
            payload={"initial_fields_count": len(input_schema)},
        ),
    )
    captured_keys: set[str] = set()

    # SCHEMA FIELD EVALUATION & CAPTURE
    # Iterates through each schema field, evaluating satisfaction against existing data
    # and recording satisfied keys into the capture set.
    for field in input_schema:
        schema_key: str | None = field.get("key")
        if schema_key and is_field_satisfied(field, existing_data, mapping):
            captured_keys.add(schema_key)

    # SCHEMA DELTA CALCULATION LOGGING
    # Logs the calculation phase prior to filtering out satisfied schema fields.
    report_status(
        state="info",
        message="Executing schema delta calculation to filter satisfied fields.",
        context=LogContext(
            component="database.filter_schema_by_keys",
            log_path=log_path,
            silent=True,
            trace_id="filter_schema_by_keys",
            actor=context.get("user"),
            payload={"captured_keys_count": len(captured_keys)},
        ),
    )

    # FIREWALL FILTERING & LIST GENERATION
    # Constructs the filtered schema list by retaining only fields whose keys have not been captured.
    filtered_schema: list[dict[str, Any]] = [
        field for field in input_schema if field.get("key") not in captured_keys
    ]

    # VALIDATION SUMMARY & FIREWALL METRICS
    # Reports a final firewall summary detailing initial field counts versus satisfied entries.
    report_status(
        state="item",
        message=f"Schema firewall summary: Processed {len(input_schema)} initial fields, {len(captured_keys)} fields satisfied and filtered.",
        context=LogContext(
            component="database.filter_schema_by_keys",
            log_path=log_path,
            silent=True,
            trace_id="filter_schema_by_keys",
            actor=context.get("user"),
            payload={
                "initial_fields": len(input_schema),
                "satisfied_fields": len(captured_keys),
                "remaining_fields": len(filtered_schema),
            },
        ),
    )

    return filtered_schema
