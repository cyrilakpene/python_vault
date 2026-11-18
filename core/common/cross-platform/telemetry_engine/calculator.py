from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: CALCULATION STACK EVALUATION
# This utility evaluates execution stack calculation formulas while enforcing dependency checks
# against missing strict keys, handling execution exceptions, and applying fault recovery defaults.
# [>] EXECUTING CALCULATION EVALUATION
def compute_calculations(
    manifest: dict[str, Any],
    calc_cfg: dict[str, Any],
    target_context: str,
    missing_strict_keys: list[str],
) -> tuple[dict[str, Any], list[str]]:
    """
    Evaluates calculation formulas across the execution stack while enforcing
    dependency checks against missing strict keys and fault recovery.

    Args:
        manifest (dict[str, Any]): The working manifest dictionary containing current execution state and data.
        calc_cfg (dict[str, Any]): Configuration mapping containing context groups and calculation formulas.
        target_context (str): The specific execution context target to evaluate alongside the global scope.
        missing_strict_keys (list[str]): A list of required strict keys that are currently missing.

    Returns:
        tuple[dict[str, Any], list[str]]: A tuple containing the updated manifest dictionary and a list of skipped calculations.
    """
    # EXECUTION STACK INITIALIZATION
    # Establishes the evaluation scope starting with the global context and appending the target context if applicable.
    execution_stack = ["global"]
    if target_context != "global" and target_context in calc_cfg:
        execution_stack.append(target_context)

    # SKIPPED CALCULATIONS TRACKER
    # Initializes a list container to record any calculations bypassed due to missing dependencies or errors.
    skipped_calcs: list[str] = []

    # STACK ITERATION & FORMULA EVALUATION
    # Iterates through each context layer in the stack, verifying callable formulas
    # and managing dependency validation or runtime exception recovery.
    for ctx in execution_stack:
        ctx_group = calc_cfg.get(ctx, {})
        for target_key, formula in ctx_group.items():
            if not callable(formula):
                continue

            # STRICT DEPENDENCY VALIDATION
            # Bypasses calculation and assigns None if any mandatory strict keys are missing.
            if missing_strict_keys:
                manifest[target_key] = None
                skipped_calcs.append(target_key)
                continue

            # FORMULA EXECUTION & FAULT RECOVERY
            # Evaluates the calculation formula against the manifest, capturing any runtime exceptions
            # and applying appropriate default fallback values based on the target key name.
            try:
                manifest[target_key] = formula(manifest)
            except Exception as e:
                manifest[target_key] = False if "trigger" in target_key else 0.0
                skipped_calcs.append(f"{target_key} (Error: {e})")

    return manifest, skipped_calcs
