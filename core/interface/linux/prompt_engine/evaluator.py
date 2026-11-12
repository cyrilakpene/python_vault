from typing import Any


# ACTION REGISTRY SUBSYSTEM: CONDITIONAL ACTION FILTERING
# This utility evaluates registered menu action conditions against the current context
# and returns a filtered dictionary containing only active and available operations.
# [>] EXECUTING ACTION FILTERING ROUTINE
def filter_active_actions(
    actions: dict[str, dict[str, Any]], context: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """
    Filters active actions whose conditions evaluate to True against the current context.

    Args:
        actions (dict[str, dict[str, Any]]): The master dictionary containing all registered action options.
        context (dict[str, Any]): The operational context dictionary evaluated against condition predicates.

    Returns:
        dict[str, dict[str, Any]]: A dictionary containing only the actions whose conditions evaluated to True.
    """
    # CONDITION EVALUATION & FILTERING
    # Iterates through each registered action item and retains only those whose condition predicate
    # evaluates to True when passed the active operational context.
    return {k: opt for k, opt in actions.items() if opt["condition"](context)}
