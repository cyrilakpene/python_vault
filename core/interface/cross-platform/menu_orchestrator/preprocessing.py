from typing import Any, Callable

from .constants import report_status, log_path  # type: ignore[import-not-found]


# OPTION PREPROCESSING & MENU INGRESS ENGINE
# This utility handles null-set verification, backward navigation injection, acronym mapping,
# casing gates, hotkey/mnemonic extraction, and interaction hint string construction for terminal menus.
# [>] EXECUTING OPTION PREPROCESSING
def preprocess_options(
    options: dict[str, Callable[..., Any]],
    title: str,
    shorthand: bool,
    batch: bool,
    ui_config: dict[str, Any] | None,
    allow_back: bool,
) -> tuple[dict[str, Callable[..., Any]], list[dict[str, Any]], str, bool]:
    """
    Handles null-set verification, backward navigation injection,
    acronym mapping, casing gates, hotkey/mnemonic extraction,
    and interaction hint string construction.

    Args:
        options: Dictionary mapping option labels to executable callback handlers.
        title: Title string describing the menu context for logging and validation.
        shorthand: Boolean flag enabling mnemonic/hotkey shorthand interpretation.
        batch: Boolean flag indicating whether multiple option selections are permitted.
        ui_config: Optional configuration dictionary containing custom UI rules and acronym maps.
        allow_back: Boolean flag determining whether to inject a backward navigation option.

    Returns:
        tuple[dict[str, Callable[..., Any]], list[dict[str, Any]], str, bool]: A tuple containing
            the updated options dictionary, structured entry metadata list, generated prompt string,
            and the resolved mnemonic flag.
    """
    # NULL-SET VERIFICATION & INGRESS ABORTION
    # Verifies whether the options dictionary is empty, reporting a warning and aborting early if true.
    if not options:
        report_status(
            state="warn",
            message=f"Ingress aborted: Null-set detected for {title!r}.",
            silent=True,
            log_path=log_path,
        )
        return {}, [], "", False

    # WORKING OPTIONS INITIALIZATION & MNEMONIC MODE RESOLUTION
    # Initializes a working copy of options and determines whether mnemonic hotkey mode is active.
    working_options = dict(options)
    is_mnemonic = shorthand or (
        ui_config is not None and ui_config.get("id_type") == "mnemonic"
    )

    # BACKWARD NAVIGATION INJECTION
    # Appends a standardized back navigation option to the working options dictionary if permitted.
    if allow_back:
        back_label = "[b]ack" if is_mnemonic else "Go Back"
        working_options[back_label] = lambda: "__BACK__"

    options_labels: list[str] = list(working_options.keys())
    entries: list[dict[str, Any]] = []
    acronym_map: dict[str, str] = (ui_config or {}).get("acronyms", {})

    # OPTION ENTRY PARSING & METADATA EXTRACTION LOOP
    # Iterates through option labels to extract hotkeys, normalize text casing, apply acronym overrides,
    # and build structured entry metadata records.
    for label in options_labels:
        hotkey = ""
        working_label = label
        if is_mnemonic:
            if "[" in label and "]" in label:
                hotkey = label.split("[")[1].split("]")[0]
                working_label = label.replace(f"[{hotkey}]", hotkey)
            else:
                hotkey = label

        if is_mnemonic:
            display_label = working_label.replace("_", " ")
        else:
            display_label = working_label.replace("_", " ").title()

        if acronym_map:
            display_label = " ".join(
                acronym_map.get(word, word) for word in display_label.split()
            )

        entries.append(
            {
                "label": display_label,
                "hotkey": hotkey,
                "action_key": label,
                "state_ref": hotkey if is_mnemonic else label,
            }
        )

    # PROMPT RANGE HINT COMPUTATION
    # Calculates the valid selection numerical range or key hints based on available entries count.
    total_entries = len(entries)
    range_hint = f"1-{total_entries}" if total_entries > 1 else "1"

    # EXAMPLE HINT GENERATION
    # Constructs representative example strings for batch or single-selection prompt displays.
    if is_mnemonic:
        example_hint = (
            ", ".join([e["hotkey"] for e in entries[:2]])
            if batch and total_entries > 1
            else (entries[0]["hotkey"] if entries else "key")
        )
    else:
        example_hint = "1, 2" if batch and total_entries > 1 else "1"

    # INTERACTION PROMPT STRING CONSTRUCTION
    # Formats the final interactive user prompt string tailored to mnemonic or numeric selection modes.
    if is_mnemonic:
        prompt_str = (
            f"Enter Keys to override (Batch) [e.g., {example_hint}]"
            if batch
            else f"Enter Key to override [e.g., {example_hint}]"
        )
    else:
        prompt_str = (
            f"Select options ({range_hint}) [e.g., {example_hint}]"
            if batch
            else f"Select option ({range_hint}) [e.g., {example_hint}]"
        )

    # PREPROCESSING MANIFEST RETURN
    # Returns the populated working options, structured entries, prompt message string, and mnemonic flag.
    return working_options, entries, prompt_str, is_mnemonic
