from typing import Any, Callable, cast


# DATA CONTAINER SUBSYSTEM: HEURISTIC RESOLUTION & OUTPUT STABILIZATION ENGINE
# This utility defines and returns a dictionary of strategy functions for resolving target nodes
# and stabilizing output values based on active feature flags and strict validation constraints.
# [>] EXECUTING HEURISTICS REGISTRY INITIALIZATION
def get_heuristics(
    path: str, features: dict[str, Any]
) -> dict[str, Callable[[Any], Any]]:
    """
    Defines strategy functions for target resolution and output stabilization.

    Args:
        path (str): The target path string associated with the heuristics context.
        features (dict[str, Any]): Feature flag configurations controlling resolution and strictness rules.

    Returns:
        dict[str, Callable[[Any], Any]]: A registry mapping heuristic identifiers ("resolve_targets",
        "stabilize_output") to their respective strategy functions.
    """

    # TARGET RESOLUTION STRATEGY
    # Determines whether to unwrap single-item dictionaries or return collections as-is
    # based on global merge and atomic flattening feature flags.
    def _resolve_targets(found: Any) -> Any:
        if features.get("global_merge", False) or not features.get(
            "flatten_atomic", True
        ):
            return found
        if isinstance(found, dict):
            found_dict = cast(dict[Any, Any], found)
            if len(found_dict) == 1:
                return next(iter(found_dict.values()))
        return cast(Any, found)

    # OUTPUT STABILIZATION STRATEGY
    # Normalizes null outputs to empty dictionaries or raises a strict validation error
    # if strict mode is enabled and a null registry is encountered.
    def _stabilize_output(out: Any) -> Any:
        if not (features.get("strict", False) and out is None):
            return out if out is not None else {}
        raise ValueError(
            f"Strict filter violation: Null registry found for path {path!r}."
        )

    return {"resolve_targets": _resolve_targets, "stabilize_output": _stabilize_output}
