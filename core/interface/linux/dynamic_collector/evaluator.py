from typing import Any

from .registry import CONDITION_OPERATORS  # type: ignore[import-not-found]
from .path_resolver import resolve_path, inject_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: RULE CONDITION EVALUATION & LOGICAL GATE ENGINE
# This utility evaluates whether specific rules are logically applicable to the current state,
# supporting implicit AND logic across condition lists, path resolution, state repair defaults, and operator lookups.
# [>] EXECUTING RULE CONDITION EVALUATION
def evaluate_rule_conditions(rule: dict[str, Any], master_dict: dict[str, Any]) -> bool:
    """
    Evaluates if the specific rule is logically applicable to the current state.
    Supports 'Implicit AND' logic: if a list is provided, all gates must pass.

    Args:
        rule (dict[str, Any]): The rule definition dictionary containing condition clauses.
        master_dict (dict[str, Any]): The master dictionary state used for path resolution and state repair.

    Returns:
        bool: True if all rule conditions pass (or if no conditions exist); False otherwise.
    """
    # CONDITION EXTRACTION & NORMALIZATION
    # Extracts raw conditions from the rule dictionary, returning True if none are specified,
    # and normalizing single condition dictionaries into a list for uniform iteration.
    raw_conditions: Any = rule.get("condition")

    if not raw_conditions:
        return True

    conditions_list: list[dict[str, Any]] = (
        [raw_conditions] if isinstance(raw_conditions, dict) else raw_conditions
    )

    # CONDITION ITERATION & PATH RESOLUTION
    # Iterates through each condition gate, resolving the target key path within the master dictionary state.
    for cond in conditions_list:
        key_path = cond.get("key", "")
        current_val = resolve_path(master_dict, key_path)

        # STATE REPAIR GATE: NORMALIZING VOID STATES
        # If the resolved value is missing or empty and a default value is defined in the condition,
        # injects the default value back into the master dictionary tree state.
        if (current_val is None or current_val == "") and "default" in cond:
            default_val = cond["default"]
            inject_path(master_dict, key_path, default_val)
            current_val = default_val

        # OPERATOR LOOKUP & LOGICAL EVALUATION
        # Retrieves target values, operator keys, and corresponding comparison functions from the global registry,
        # returning False immediately if any condition check fails.
        target_val = cond.get("value")
        op_key = cond.get("operator", "==")

        check_func = CONDITION_OPERATORS.get(op_key)

        if not (check_func and check_func(current_val, target_val)):
            return False

    return True
