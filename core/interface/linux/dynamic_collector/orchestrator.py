from typing import Any, Callable

from .evaluator import evaluate_rule_conditions  # type: ignore[import-not-found]
from .path_resolver import inject_path  # type: ignore[import-not-found]
from .registry import CONDITION_OPERATORS  # type: ignore[import-not-found]
from .constants import report_status, user_input, log_path  # type: ignore[import-not-found]


# DATA INGESTION SUBSYSTEM: DYNAMIC POLICY RECONCILIATION & INPUT COLLECTION
# This utility manages high-performance memory state ingestion, evaluating policy rules,
# running schema filtering, collecting interactive user inputs, and applying state transformations.
# [>] EXECUTING DYNAMIC INPUT COLLECTION & POLICY RECONCILIATION
def collect_dynamic_inputs(
    master_dict: dict[str, Any],
    policy_sequence: list[dict[str, Any]],
    mapping: dict[str, str] | None = None,
    use_filter: bool = True,
    display_banner: bool | None = None,
    critical: bool = False,
    filter_func: Callable[..., list[dict[str, Any]]] | None = None,
) -> tuple[dict[str, Any], str]:
    """
    A high-performance ingestion engine that reconciles memory states against a policy sequence.
    Requires schema filtering callables to be passed explicitly as arguments when enabled.

    Args:
        master_dict (dict[str, Any]): The primary memory state dictionary being updated.
        policy_sequence (list[dict[str, Any]]): A list of policy rules governing ingestion.
        mapping (dict[str, str] | None): Optional source-to-target mapping dictionary.
        use_filter (bool): Flag to determine whether to apply schema filtering.
        display_banner (bool | None): Optional flag controlling status banner visibility.
        critical (bool): Default criticality flag applied to target schema fields.
        filter_func (Callable[..., list[dict[str, Any]]] | None): Optional custom filter function.

    Returns:
        tuple[dict[str, Any], str]: The updated master dictionary and a status completion token.
    """
    # INITIALIZATION STATUS LOGGING
    # Reports status for initializing the local logic registry and available operators.
    report_status(
        state="task",
        message="INITIALIZING LOCAL LOGIC REGISTRY.",
        log_path=log_path,
        silent=True,
    )

    report_status(
        state="item",
        message=f"Registry loaded: {', '.join(CONDITION_OPERATORS.keys())} operators available.",
        log_path=log_path,
        silent=True,
    )

    report_status(
        state="proc",
        message="Executing policy reconciliation...",
        log_path=log_path,
        silent=True,
    )

    # POLICY SEQUENCE ITERATION LOOP
    # Iterates through each policy rule in the sequence to evaluate conditions and collect inputs.
    for rule in policy_sequence:
        rule_label: str = rule.get("label", "UNDEFINED").upper()

        report_status(
            state="info",
            message=f"Evaluating rule applicability: {rule_label!r}.",
            log_path=log_path,
            silent=True,
        )

        # RULE APPLICABILITY EVALUATION CHECK
        # Skips the current rule if its conditions are not met by the master state dictionary.
        if not evaluate_rule_conditions(rule, master_dict):
            report_status(
                state="info",
                message=f"Evaluation failed: Skipping {rule_label!r}.",
                log_path=log_path,
                silent=True,
            )
            continue

        target_schema: list[dict[str, Any]] = rule["schema"]

        report_status(
            state="info",
            message=f"Engaging deduplication firewall: {rule_label!r}.",
            log_path=log_path,
            silent=True,
        )

        # SCHEMA DEDUPLICATION & FILTERING
        # Applies the custom filter function if enabled and provided to purge redundant schema fields.
        if use_filter and filter_func is not None:
            original_count = len(target_schema)
            target_schema = filter_func(
                input_schema=target_schema, existing_data=master_dict, mapping=mapping
            )

            report_status(
                state="item",
                message=f"Purgation delta: {original_count} fields -> {len(target_schema)} remaining.",
                log_path=log_path,
                silent=True,
            )

        # IDEMPOTENT COMPLETION CHECK
        # Skips processing if the filtered target schema is empty, meaning the master dict already satisfies the rule.
        if not target_schema:
            report_status(
                state="item",
                message=f"Idempotent skip: Master dict already satisfies {rule_label!r}.",
                log_path=log_path,
                silent=True,
            )
            continue

        # BANNER DISPLAY CONDITIONAL
        if display_banner is True:
            report_status(
                state="info",
                message=f"Processing logic block: {rule_label!r}.",
                log_path=log_path,
            )

        report_status(
            state="info",
            message=f"Input required: Collecting {len(target_schema)} fields for {rule_label!r}.",
            log_path=log_path,
            silent=True,
        )

        # FIELD CRITICALITY ASSIGNMENT
        # Ensures all fields in the target schema have a defined critical status.
        for field in target_schema:
            if "critical" not in field:
                field["critical"] = critical

        # INTERACTIVE INPUT COLLECTION
        # Invokes user input collection for the filtered target schema.
        new_data: dict[str, Any] = user_input(
            target_schema,
            silent=True,
        )

        # RULE TRANSFORMATION INJECTION
        # Applies any specified transform rules to the master state dictionary.
        if "transform" in rule:
            for transform_key, final_val in rule["transform"].items():
                report_status(
                    state="item",
                    message=f"State transform: {transform_key!r} mapped to {final_val!r}.",
                    log_path=log_path,
                    silent=True,
                )
                inject_path(master_dict, transform_key, final_val)

        report_status(
            state="info",
            message=f"Synchronizing memory state.",
            log_path=log_path,
            silent=True,
        )

        # MEMORY STATE SYNCHRONIZATION
        # Updates the master dictionary with newly collected input data.
        master_dict.update(new_data)

        report_status(
            state="item",
            message=f"Memory sync: Integrated {len(new_data)} new keys into master state.",
            log_path=log_path,
            silent=True,
        )

        report_status(
            state="done",
            message=f"STEP COMPLETE: {rule_label!r}",
            log_path=log_path,
            silent=True,
        )
        return master_dict, "STEP_COMPLETE"

    # ALL POLICIES SATISFIED EXIT
    report_status(
        state="done", message="ALL POLICIES SATISFIED", log_path=log_path, silent=True
    )
    return master_dict, "ALL_STEPS_COMPLETE"
