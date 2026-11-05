from typing import Any

from .operators import get_operators  # type: ignore[import-not-found]
from .extractor import resolve_field_value  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: STANDARDIZED SYNCHRONIZER & RECONCILIATION ENGINE
# This utility reconciles state between master schema templates and live data pools using rule mappings,
# tracking state population versus modification flags during synchronization.
# [>] EXECUTING SCHEMA SYNCHRONIZATION & RECONCILIATION
def synchronize_schema_by_rules(
    master_dict: dict[str, Any],
    existing_data: dict[str, Any],
    mapping: dict[str, dict[str, Any]],
    keep_existing: bool = False,
) -> tuple[dict[str, Any], bool, bool]:
    """
    Standardized Synchronizer: Reconciles state between a template and live data.

    Args:
        master_dict (dict[str, Any]): The target master dictionary state to synchronize.
        existing_data (dict[str, Any]): The live data pool container to extract values from.
        mapping (dict[str, dict[str, Any]]): The mapping configuration linking target keys to source rules.
        keep_existing (bool, optional): Flag to preserve existing non-empty values. Defaults to False.

    Returns:
        tuple[dict[str, Any], bool, bool]: A tuple containing the updated state dictionary,
        along with population and modification boolean status flags.
    """
    # OPERATOR REGISTRY & STATE INITIALIZATION
    # Reports initialization of reconciliation operators, instantiates active logic gates via get_operators(),
    # and creates a copy of the master dictionary state alongside tracking flags.
    report_status(
        state="task",
        message="Initializing schema reconciliation operators and configuration state.",
        context=LogContext(
            component="database.synchronize_schema_by_rules",
            log_path=log_path,
            silent=True,
            trace_id="synchronize_schema_by_rules",
            actor=context.get("user"),
            payload={"mapping_keys_count": len(mapping)},
        ),
    )

    operators = get_operators()
    updated_state: dict[str, Any] = master_dict.copy()
    is_populated: bool = False
    is_modified: bool = False

    report_status(
        state="info",
        message=f"Schema synchronizer ready: {len(operators)} active logic gates loaded.",
        context=LogContext(
            component="database.synchronize_schema_by_rules",
            log_path=log_path,
            silent=True,
            trace_id="synchronize_schema_by_rules",
            actor=context.get("user"),
            payload={"operators_count": len(operators)},
        ),
    )

    # MAPPING ITERATION & FIELD RESOLUTION
    # Iterates through each target key and configuration rule in the mapping dictionary,
    # resolving values while respecting collision guards and conditional valves.
    for target_key, config in mapping.items():
        # Check collision guard & extract value via modules
        extracted_val = resolve_field_value(
            target_key,
            config,
            existing_data,
            updated_state,
            keep_existing,
            operators,
        )

        # STATE RECONCILIATION & MUTATION TRACKING
        # Compares resolved values against current state values, categorizing changes
        # as either fresh population of empty fields or updates to existing values.
        if extracted_val is not None:
            current_val = updated_state.get(target_key)

            # Mutation tracking: Populating vs Modifying
            if current_val in [None, "", [], {}, False]:
                if extracted_val not in [None, "", [], {}, False]:
                    report_status(
                        state="item",
                        message=f"Schema population: Field {target_key!r} successfully injected with resolved value.",
                        context=LogContext(
                            component="database.synchronize_schema_by_rules",
                            log_path=log_path,
                            silent=True,
                            trace_id="synchronize_schema_by_rules",
                            actor=context.get("user"),
                            payload={"target_key": target_key},
                        ),
                    )
                    updated_state[target_key] = extracted_val
                    is_populated = True
            elif current_val != extracted_val:
                report_status(
                    state="info",
                    message=f"Schema modification: Field {target_key!r} updated from {current_val!r} to {extracted_val!r}.",
                    context=LogContext(
                        component="database.synchronize_schema_by_rules",
                        log_path=log_path,
                        silent=True,
                        trace_id="synchronize_schema_by_rules",
                        actor=context.get("user"),
                        payload={
                            "target_key": target_key,
                            "old_value": current_val,
                            "new_value": extracted_val,
                        },
                    ),
                )
                updated_state[target_key] = extracted_val
                is_modified = True

    # RECONCILIATION COMPLETION & STATUS REPORTING
    # Logs completion of the reconciliation cycle and returns the updated state along with tracking flags.
    report_status(
        state="done",
        message=f"Schema reconciliation complete.",
        context=LogContext(
            component="database.synchronize_schema_by_rules",
            log_path=log_path,
            silent=True,
            trace_id="synchronize_schema_by_rules",
            actor=context.get("user"),
            payload={"is_populated": is_populated, "is_modified": is_modified},
        ),
    )
    return updated_state, is_populated, is_modified
