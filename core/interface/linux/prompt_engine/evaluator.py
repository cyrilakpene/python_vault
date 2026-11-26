from typing import Any

from .constants import report_status, LogContext, log_path, context  # type: ignore[import-not-found]


# ACTION REGISTRY SUBSYSTEM: CONDITIONAL ACTION FILTERING & VALIDATION
# This utility evaluates registered menu action conditions against the current context
# with safe lookup handling and returns a filtered dictionary containing only active operations.
# [>] EXECUTING CONDITIONAL ACTION FILTERING ROUTINE
def filter_active_actions(
    actions: dict[str, dict[str, Any]], state_context: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """
    Filters active actions whose conditions evaluate to True against the current context.

    Args:
        actions (dict[str, dict[str, Any]]): The master dictionary containing all registered action options.
        state_context (dict[str, Any]): The operational context dictionary evaluated against condition predicates.

    Returns:
        dict[str, dict[str, Any]]: A dictionary containing only the actions whose conditions evaluated to True or are unconstrained.
    """
    # INITIALIZATION: FILTERED ACTIONS CONTAINER
    # Instantiates an empty dictionary to store the validated and active action options.
    filtered_actions: dict[str, Any] = {}

    # ACTION ITERATION & CONDITION EVALUATION
    # Iterates through each registered action item, extracting its condition predicate.
    # Retains the action if no condition is specified or if the condition predicate evaluates to True against the context.
    for k, opt in actions.items():
        condition = opt.get("condition")
        if condition is None:
            filtered_actions[k] = opt
            continue

        try:
            if condition(state_context):
                filtered_actions[k] = opt
        except Exception as exc:
            # CONDITION EVALUATION ERROR REPORTING
            # Emits a warning status when a condition predicate raises an exception during evaluation.
            report_status(
                state="warn",
                message=f"Condition evaluation failed for action '{k}': {exc}.",
                context=LogContext(
                    component="prompt_engine",
                    log_path=log_path,
                    trace_id="interface.prompt_engine",
                    actor=context.get("user"),
                    exception=str(exc),
                    payload={
                        "action_key": k,
                    },
                ),
            )

    # FILTERED ACTIONS RETURN
    # Returns the compiled dictionary of active menu actions.
    return filtered_actions
