import inspect
from typing import Any, Callable

from .constants import report_status, log_path  # type: ignore[import-not-found]


# TOKEN DISPATCH & EXECUTION ROUTING ENGINE
# This utility normalizes operator input tokens (single or batch), maps symbols back to functional vectors,
# inspects target function signatures to conditionally inject telemetry state, and handles execution boundaries.
# [>] EXECUTING TOKEN DISPATCH & ROUTING
def dispatch_tokens(
    raw_selection: Any,
    entries: list[dict[str, Any]],
    working_options: dict[str, Callable[..., Any]],
    is_mnemonic: bool,
    batch: bool,
    state: dict[str, Any] | None,
) -> Any:
    """
    Normalizes operator input tokens (single or batch), maps symbols back to functional vectors,
    inspects target function signatures to conditionally inject telemetry state, and handles execution boundaries.

    Args:
        raw_selection: Raw user selection input (string, integer, or list of tokens).
        entries: List of structured entry dictionaries containing hotkeys and action keys.
        working_options: Dictionary mapping action keys to executable callback functions.
        is_mnemonic: Boolean flag indicating whether mnemonic key lookup mode is active.
        batch: Boolean flag indicating whether batch multi-selection processing is permitted.
        state: Optional state dictionary container for telemetry injection.

    Returns:
        Any: The execution result of the invoked callback(s), a list of results in batch mode, or "BACK" if navigating backward.
    """
    # TOKEN NORMALIZATION & LIST CONVERSION
    # Normalizes raw user selection inputs into a standardized lowercase string list container
    # for consistent batch or single-token iteration.
    tokens = (
        [str(t).lower().strip() for t in raw_selection]  # type: ignore[arg-type]
        if isinstance(raw_selection, list)
        else [str(raw_selection).lower().strip()]
    )

    selected_results: list[Any] = []

    # SELECTION TOKEN ITERATION & LOOKUP LOOP
    # Iterates through each selection token, performing either mnemonic hotkey matching
    # or numeric index parsing depending on the active mode.
    for selection_str in tokens:
        idx: int = -1

        if is_mnemonic:
            idx = next(
                (
                    i
                    for i, e in enumerate(entries)
                    if e["hotkey"].lower() == selection_str
                ),
                -1,
            )
        else:
            try:
                idx = int(selection_str) - 1
            except (ValueError, TypeError):
                idx = -1

        # BOUNDS VERIFICATION & SIGNATURE INSPECTION
        # Validates whether the resolved index falls within valid entry bounds, retrieves the target callback,
        # and inspects its parameter signature to determine if telemetry state injection is required.
        if 0 <= idx < len(entries):
            target_entry = entries[idx]
            target_label = target_entry["action_key"]
            target_func: Callable[..., Any] = working_options[target_label]

            sig: inspect.Signature = inspect.signature(target_func)
            params = list(sig.parameters.values())

            wants_state: bool = any(
                p.name == "state"
                or (p.annotation is dict or "dict" in str(p.annotation).lower())
                for p in params
            )

            # CONDITIONAL STATE INJECTION & CALLBACK EXECUTION
            # Invokes the target callback function with or without the active state dictionary
            # based on signature inspection results, appending the output to results collection.
            if wants_state and params:
                active_state = state if state is not None else {}
                selected_results.append(target_func(active_state))
            else:
                selected_results.append(target_func())
        else:
            report_status(
                state="fail",
                message=f"Routing error: Choice {selection_str!r} out of bounds.",
                log_path=log_path,
            )

    # OUTPUT BATCH RESOLUTION & BACKWARD NAVIGATION CHECK
    # Consolidates results into a list for batch mode or a single value otherwise,
    # returning a 'BACK' signal if the backward navigation option was triggered.
    resolved_output = (
        selected_results
        if batch
        else (selected_results[0] if selected_results else None)
    )

    if resolved_output == "__BACK__":
        return "BACK"

    return resolved_output
