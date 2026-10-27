from typing import Any, Callable

from typing import Any, Callable

# DATA CONTAINER SUBSYSTEM: GLOBAL CONDITION OPERATORS REGISTRY
# This constant dictionary defines global condition operators and comparison lambdas
# used across data filtering, rule evaluation, and condition matching pipelines.
# [>] INITIALIZING GLOBAL CONDITION OPERATORS REGISTRY
CONDITION_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    # EQUALITY & INEQUALITY OPERATORS
    # Compares current and target values for exact equality or inequality.
    "==": lambda current, target: current == target,
    "!=": lambda current, target: current != target,
    # NUMERICAL COMPARISON OPERATORS
    # Performs strict type-checked numerical comparison evaluations.
    ">": lambda current, target: isinstance(current, (int, float)) and current > target,
    "<": lambda current, target: isinstance(current, (int, float)) and current < target,
    ">=": lambda current, target: isinstance(current, (int, float))
    and current >= target,
    "<=": lambda current, target: isinstance(current, (int, float))
    and current <= target,
    # CONTAINER MEMBERSHIP OPERATORS
    # Safely evaluates whether the current value exists or does not exist within a target collection (list, set, str).
    "in": lambda current, target: (
        current in target if isinstance(target, (list, set, str)) else False
    ),
    "not in": lambda current, target: (
        current not in target if isinstance(target, (list, set, str)) else True
    ),
}
