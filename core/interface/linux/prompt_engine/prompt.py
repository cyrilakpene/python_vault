from typing import Any

from .evaluator import filter_active_actions  # type: ignore[import-not-found]
from .constants import report_status, LogContext, user_input, log_path, context  # type: ignore[import-not-found]


# ACTION REGISTRY SUBSYSTEM: DYNAMIC PROMPT BUILDER & USER INPUT GATE
# This utility constructs dynamic interactive prompt labels from action options,
# manages default selection flags, and collects operator choices via the user input gateway.
# [>] EXECUTING DYNAMIC PROMPT BUILDER & INGRESS GATE
def build_and_prompt(
    options: dict[str, dict[str, Any]],
    fallback_default: str = "c",
    state_context: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Builds dynamic prompt labels and collects user input via user_input schema.

    Args:
        options (dict[str, dict[str, Any]]): A dictionary of action options available for selection.
        fallback_default (str, optional): The fallback default selection key if no option is explicitly flagged. Defaults to "c".
        state_context (dict[str, Any] | None, optional): Optional runtime context evaluated against option conditions. Defaults to None.

    Returns:
        tuple[str, str]: The chosen user selection key and the default key.
    """
    # ACTIVE OPTION FILTERING
    # Evaluates option conditions against runtime context when provided so inactive options are excluded.
    active_options = (
        filter_active_actions(options, state_context)
        if state_context is not None
        else options
    )

    # EMPTY ACTIVE OPTIONS WARNING CHECK
    # Emits a warning status if filtering leaves no active options available to present.
    if not active_options:
        report_status(
            state="warn",
            message=(
                f"No active options available for prompt; falling back to default "
                f"{fallback_default!r}."
            ),
            context=LogContext(
                component="prompt_engine",
                log_path=log_path,
                trace_id="interface.prompt_engine",
                actor=context.get("user"),
                payload={
                    "total_options": len(options),
                    "fallback_default": fallback_default,
                },
            ),
        )

    # INITIALIZATION: LABEL COLLECTION & DEFAULT SETUP
    # Instantiates an empty list for prompt labels and sets the initial default key to the provided fallback value.
    labels: list[str] = []
    default_key = fallback_default

    # OPTION ITERATION & LABEL FORMATTING
    # Iterates through active action options, identifying default selections, formatting bracketed hotkeys,
    # and appending status markers.
    for key, opt in active_options.items():
        if opt.get("default", False):
            default_key = key
            labels.append(f"[{key}]{opt['label']} (default)")
        else:
            labels.append(f"[{key}]{opt['label']}")

    # PROMPT MESSAGE ASSEMBLY
    # Joins all formatted option labels with pipe separators and appends a question mark.
    prompt_message = " | ".join(labels) + "?"

    # INGRESS GATE EXECUTION: USER INPUT COLLECTION
    # Triggers a silent interactive user input prompt using the compiled choice schema and prompt message.
    feedback = user_input(
        schema=[
            {
                "key": "choice",
                "label": prompt_message,
                "cast": "str",
                "default": default_key,
            }
        ],
        silent=True,
    )

    # CHOICE EXTRACTION & NORMALIZATION
    # Extracts the operator's choice from the feedback dictionary, falling back to the default key and casting to lowercase.
    choice = str(feedback.get("choice", default_key)).lower()
    return choice, default_key
