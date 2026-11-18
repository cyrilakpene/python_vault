from typing import Any

from .constants import user_input  # type: ignore[import-not-found]


# ACTION REGISTRY SUBSYSTEM: DYNAMIC PROMPT BUILDER & USER INPUT GATE
# This utility constructs dynamic interactive prompt labels from action options,
# manages default selection flags, and collects operator choices via the user input gateway.
# [>] EXECUTING DYNAMIC PROMPT BUILDER & INGRESS GATE
def build_and_prompt(
    options: dict[str, dict[str, Any]], fallback_default: str = "c"
) -> tuple[str, str]:
    """
    Builds dynamic prompt labels and collects user input via user_input schema.

    Args:
        options (dict[str, dict[str, Any]]): A dictionary of filtered action options available for selection.
        fallback_default (str, optional): The fallback default selection key if no option is explicitly flagged. Defaults to "c".

    Returns:
        tuple[str, str]: The chosen user selection key and the default key.
    """
    # INITIALIZATION: LABEL COLLECTION & DEFAULT SETUP
    # Instantiates an empty list for prompt labels and sets the initial default key to the provided fallback value.
    labels: list[str] = []
    default_key = fallback_default

    # OPTION ITERATION & LABEL FORMATTING
    # Iterates through action options, identifying default selections, formatting bracketed hotkeys,
    # and appending status markers.
    for key, opt in options.items():
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
