from typing import Any, Callable


# DATA CONTAINER SUBSYSTEM: SAFE TYPE CASTING & STRING CONVERSION UTILITY
# This utility provides a clean, safe wrapper for casting arbitrary data values
# into their respective string representations for formatting and output buffers.
# [>] EXECUTING SAFE STRING CONVERSION
def _to_string(value: Any) -> str:
    """
    Safely converts an arbitrary data value into its string representation.

    Args:
        value (Any): The input value or object to cast.

    Returns:
        str: The string representation of the input value.
    """
    # STRING CASTING RESOLUTION
    # Invokes the built-in string constructor on the provided value.
    return str(value)


# DATA CONTAINER SUBSYSTEM: RULE ENFORCEMENT & LOGIC GATE OPERATOR REGISTRY
# This utility defines and returns a dictionary of core comparison operators and rule evaluation gates
# used for schema validation, condition matching, and rule enforcement pipelines.
# [>] EXECUTING LOGIC OPERATOR REGISTRY INITIALIZATION
def get_operators() -> dict[str, Callable[[Any, Any], bool]]:
    """
    Returns the dictionary of active logic gates for rule enforcement.

    Returns:
        dict[str, Callable[[Any, Any], bool]]: A registry mapping string operator symbols
        to lambda evaluation functions.
    """
    # OPERATOR REGISTRY INITIALIZATION
    # Defines core comparative and containment operations (equality, inequality, numerical comparisons,
    # and safe collection membership checks) along with robust non-empty validation filters.
    operators: dict[str, Callable[[Any, Any], bool]] = {
        "==": lambda current, target: current == target,
        "!=": lambda current, target: current != target,
        ">": lambda current, target: isinstance(current, (int, float))
        and current > target,
        "<": lambda current, target: isinstance(current, (int, float))
        and current < target,
        "in": lambda current, target: (
            current in target if isinstance(target, (list, dict, set, str)) else False
        ),
        "is_not_empty": lambda current, _: (
            current not in [None, "", [], {}, False, 0, "0"]
            and (
                not isinstance(current, (list, dict))
                or len(_to_string(current).strip("[]{}'\" ")) > 0
            )
        ),
    }

    # MULTI-CHECK COMPOSITE RULE GATE
    # Registers a composite operator that evaluates multiple rule constraints simultaneously
    # using all() across supported operator definitions.
    operators["multi_check"] = lambda current, rules: all(
        operators[op](current, val) for op, val in rules.items() if op in operators
    )

    return operators
