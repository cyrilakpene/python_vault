from typing import Any


# ACTION REGISTRY SUBSYSTEM: CONDITIONAL ACTION FILTERING & VALIDATION
# This utility evaluates registered menu action conditions against the current context
# with safe lookup handling and returns a filtered dictionary containing only active operations.
# [>] EXECUTING CONDITIONAL ACTION FILTERING ROUTINE
def filter_active_actions(
    actions: dict[str, dict[str, Any]], context: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """
    Filters active actions whose conditions evaluate to True against the current context.

    Args:
        actions (dict[str, dict[str, Any]]): The master dictionary containing all registered action options.
        context (dict[str, Any]): The operational context dictionary evaluated against condition predicates.

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
        if condition is None or condition(context):
            filtered_actions[k] = opt

    # FILTERED ACTIONS RETURN
    # Returns the compiled dictionary of active menu actions.
    return filtered_actions
