from typing import Any


# UI SCHEMA BUILDER & LAYOUT METADATA ENGINE
# This utility merges layout defaults with user configuration overrides, constructs section specifications,
# injects 2D grid spatial properties, and builds structured UI schema dictionaries for terminal rendering engines.
# [>] EXECUTING UI SCHEMA BUILD
def build_ui_schema(
    title: str,
    entries: list[dict[str, Any]],
    is_mnemonic: bool,
    shorthand: bool,
    template: str | None,
    ui_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Merges layout defaults with ui_config overrides, constructs section specifications,
    injects 2D grid spatial properties, and defines user_input validation field constraints.

    Args:
        title: Title string describing the UI task or menu context.
        entries: List of structured entry dictionaries containing option labels and hotkeys.
        is_mnemonic: Boolean flag indicating whether mnemonic key selection mode is enabled.
        shorthand: Boolean flag enabling multi-column shorthand grid layouts.
        template: Optional custom string template for rendering menu rows.
        ui_config: Optional configuration dictionary containing custom layout and spatial overrides.

    Returns:
        tuple[dict[str, Any], dict[str, Any]]: A tuple containing the fully constructed UI schema dictionary
            and the resolved layout defaults dictionary.
    """
    # TEMPLATE RESOLUTION & DEFAULT FALLBACK
    # Determines the active row template based on explicit arguments, configuration overrides,
    # or intelligent defaults tailored to mnemonic versus numeric selection modes.
    if not template:
        template = (ui_config or {}).get("row_template")
        if not template:
            template = "[{key}] {label:<16}" if is_mnemonic else "{key:<2}. {label}"

    # LAYOUT DEFAULTS INITIALIZATION & CONFIGURATION OVERRIDES
    # Establishes base layout defaults for identifier types and column counts,
    # updating them with any custom values provided in the UI configuration.
    layout_defaults: dict[str, Any] = {
        "id_type": "mnemonic" if is_mnemonic else "auto_int",
        "cols": 2 if shorthand else 1,
        "row_template": template,
    }

    if ui_config:
        layout_defaults.update(ui_config)

    # SECTION SPECIFICATION CONSTRUCTION
    # Builds the base section specification dictionary using resolved layout properties and entry items.
    section_spec: dict[str, Any] = {
        "id_type": layout_defaults["id_type"],
        "cols": layout_defaults["cols"],
        "row_template": layout_defaults["row_template"],
        "entries": entries,
    }

    # SPATIAL & GRID PROPERTY INJECTION
    # Iterates through recognized 2D grid and box styling keys, injecting them into the section specification
    # if present within the resolved layout configuration.
    for spatial_key in (
        "id",
        "x",
        "y",
        "w",
        "h",
        "z_index",
        "stack_below",
        "has_box",
        "border_style",
        "raw_block",
    ):
        if spatial_key in layout_defaults:
            section_spec[spatial_key] = layout_defaults[spatial_key]

    # UI SCHEMA MANIFEST ASSEMBLY & RETURN
    # Packages the section specification and metadata task message into a unified UI schema structure
    # and returns it alongside the layout defaults.
    ui_schema: dict[str, Any] = {
        "metadata": {
            "task_msg": title,
            "prompt": None,
        },
        "sections": [section_spec],
    }

    return ui_schema, layout_defaults
