import inspect
from typing import Any, Callable, cast

from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# TOKEN DISPATCH & EXECUTION ROUTING ENGINE
# This utility normalizes operator input tokens (single or batch), maps symbols back to functional vectors,
# inspects target function signatures to conditionally inject telemetry state, dynamic context, or multiple dictionary arguments,
# and handles execution boundaries seamlessly.
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
    inspects target function signatures to dynamically inject state, dynamic context, or multiple arguments,
    and handles execution boundaries.

    Args:
        raw_selection: Raw user selection input (string, integer, or list of tokens).
        entries: List of structured entry dictionaries containing hotkeys and action keys.
        working_options: Dictionary mapping action keys to executable callback functions.
        is_mnemonic: Boolean flag indicating whether mnemonic key lookup mode is active.
        batch: Boolean flag indicating whether batch multi-selection processing is permitted.
        state: Optional state dictionary container for telemetry injection or dynamic argument routing.

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
        # and inspects its parameter signature to dynamically bind and inject arguments.
        if 0 <= idx < len(entries):
            target_entry = entries[idx]
            target_label = target_entry["action_key"]
            target_func: Callable[..., Any] = working_options[target_label]

            sig: inspect.Signature = inspect.signature(target_func)
            params = list(sig.parameters.values())

            active_state = state if state is not None else {}

            # DYNAMIC CONTEXT POOL PREPARATION
            # Assembles available execution context parameters into a unified lookup map.
            context_pool: dict[str, Any] = {
                "state": active_state,
                "selection": selection_str,
                "token": selection_str,
                "raw_selection": selection_str,
                "entry": target_entry,
                "batch": batch,
            }

            # Unpacks additional top-level dictionaries present in state into the context pool
            # so custom callback arguments (e.g., config, profile, options) bind dynamically.
            for k, v in active_state.items():
                if k not in context_pool:
                    context_pool[k] = v

            bound_kwargs: dict[str, Any] = {}
            unmapped_params: list[inspect.Parameter] = []

            # PARAMETER MATCHING & RESOLUTION LOOP
            # Iterates over signature parameters to bind matching keys from the context pool or capture unmapped inputs.
            for p in params:
                if p.name in context_pool:
                    bound_kwargs[p.name] = context_pool[p.name]
                elif p.kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ):
                    unmapped_params.append(p)

            # CALLBACK EXECUTION & FALLBACK RESOLUTION
            # Binds parameters dynamically by name, falls back to positional dictionary unpacking for external handlers,
            # or defaults to zero-argument invocation.
            try:
                if bound_kwargs and len(bound_kwargs) == len(params):
                    # Fully mapped keyword binding
                    bound = sig.bind_partial(**bound_kwargs)
                    bound.apply_defaults()
                    selected_results.append(target_func(*bound.args, **bound.kwargs))
                elif (
                    unmapped_params
                    and len(params) == 1
                    and unmapped_params[0].default is inspect.Parameter.empty
                ):
                    # Single unmapped positional parameter (legacy state handler)
                    selected_results.append(target_func(active_state))
                elif unmapped_params and all(
                    p.annotation is dict or "dict" in str(p.annotation).lower()
                    for p in unmapped_params
                ):
                    # Unmapped positional parameters expecting multiple dictionaries:
                    # Extracts nested dict values from state or passes state as positional fallback.
                    pos_args: list[dict[str, Any]] = [
                        cast(dict[str, Any], v)
                        for v in active_state.values()
                        if isinstance(v, dict)
                    ]
                    if len(pos_args) >= len(unmapped_params):
                        selected_results.append(
                            target_func(*pos_args[: len(unmapped_params)])
                        )
                    else:
                        selected_results.append(target_func(active_state))
                elif bound_kwargs:
                    # Partial keyword binding with remaining default values
                    bound = sig.bind_partial(**bound_kwargs)
                    bound.apply_defaults()
                    selected_results.append(target_func(*bound.args, **bound.kwargs))
                else:
                    # Default zero-argument fallback execution
                    selected_results.append(target_func())
            except (TypeError, ValueError) as e:
                report_status(
                    state="warn",
                    message=f"Binding warning for {target_label!r}: {e}. Executing fallback.",
                    context=LogContext(
                        component="interface.menu_controller",
                        log_path=log_path,
                        silent=False,
                        trace_id="menu_controller",
                        actor=context.get("user"),
                        exception=str(e),
                        payload={
                            "target_label": target_label,
                            "selection_token": selection_str,
                        },
                    ),
                )
                if params:
                    selected_results.append(target_func(active_state))
                else:
                    selected_results.append(target_func())
        else:
            report_status(
                state="fail",
                message=f"Routing error: Choice {selection_str!r} out of bounds.",
                context=LogContext(
                    component="interface.menu_controller",
                    log_path=log_path,
                    silent=False,
                    trace_id="menu_controller",
                    actor=context.get("user"),
                    payload={
                        "selection_token": selection_str,
                        "entries_count": len(entries),
                    },
                ),
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
