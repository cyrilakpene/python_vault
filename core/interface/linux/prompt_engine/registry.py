from typing import Any, Callable


# STEP REGISTRY SUBSYSTEM: DYNAMIC PIPELINE STEP REGISTRATION
# This utility dynamically registers execution steps, handlers, and processing modes into the pipeline steps master registry.
# [>] EXECUTING STEP REGISTRATION ROUTINE
def register_step(
    steps: dict[str, dict[str, Any]],
    key: str,
    label: str | None,
    handler: Callable[..., tuple[str | None, dict[str, Any]]],
    mode: str = "interactive",
) -> None:
    """
    Registers a new pipeline step dynamically into the steps master registry.

    Args:
        steps (dict[str, dict[str, Any]]): The master dictionary containing registered step mappings.
        key (str): Unique identifier key for the pipeline step.
        label (str | None): Human-readable text label describing the workflow step.
        handler (Callable[..., tuple[str | None, dict[str, Any]]]): Callable handler routine executed when the step is invoked.
        mode (str, optional): Operational execution mode (e.g., "interactive", "batch"). Defaults to "interactive".

    Returns:
        None: Modifies the steps dictionary in place.
    """
    # REGISTRY MUTATION: STEP RECORD INSERTION
    # Assigns the dictionary containing metadata keys, human-readable labels, execution handlers,
    # and operational modes to the specified step key in the master registry.
    steps[key] = {
        "key": key,
        "label": label,
        "handler": handler,
        "mode": mode,
    }
