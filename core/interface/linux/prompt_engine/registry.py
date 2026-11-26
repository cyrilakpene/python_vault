from typing import Any, Callable

from .constants import report_status, LogContext, log_path, context  # type: ignore[import-not-found]


# STEP REGISTRY SUBSYSTEM: DYNAMIC PIPELINE STEP REGISTRATION
# This utility dynamically registers execution steps, handlers, and processing modes into the pipeline steps master registry.
# [>] EXECUTING STEP REGISTRATION ROUTINE
def register_step(
    steps: dict[str, dict[str, Any]],
    key: str,
    label: str | None,
    handler: Callable[..., tuple[str | None, dict[str, Any]]],
    mode: str = "interactive",
    condition: Callable[[dict[str, Any]], bool] | None = None,
) -> None:
    """
    Registers a new pipeline step dynamically into the steps master registry.

    Args:
        steps (dict[str, dict[str, Any]]): The master dictionary containing registered step mappings.
        key (str): Unique identifier key for the pipeline step.
        label (str | None): Human-readable text label describing the workflow step.
        handler (Callable[..., tuple[str | None, dict[str, Any]]]): Callable handler routine executed when the step is invoked.
        mode (str, optional): Operational execution mode (e.g., "interactive", "automatic", "batch"). Defaults to "interactive".
        condition (Callable[[dict[str, Any]], bool] | None, optional): Optional predicate evaluated against runtime context. Defaults to None.

    Returns:
        None: Modifies the steps dictionary in place.
    """
    # DUPLICATE KEY WARNING CHECK
    # Emits a warning status if an existing step key is being overwritten in the registry.
    if key in steps:
        report_status(
            state="warn",
            message=f"Overwriting existing registered step '{key}'.",
            context=LogContext(
                component="prompt_engine",
                log_path=log_path,
                trace_id="interface.prompt_engine",
                actor=context.get("user"),
                payload={
                    "step_key": key,
                    "mode": mode,
                },
            ),
        )

    # REGISTRY MUTATION: STEP RECORD INSERTION
    # Assigns the dictionary containing metadata keys, human-readable labels, execution handlers,
    # operational modes, and optional conditions to the specified step key in the master registry.
    step_entry: dict[str, Any] = {
        "key": key,
        "label": label,
        "handler": handler,
        "mode": mode,
    }
    if condition is not None:
        step_entry["condition"] = condition

    steps[key] = step_entry
