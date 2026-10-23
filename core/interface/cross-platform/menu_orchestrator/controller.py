import inspect
from typing import Any, Callable

from .constants import heuristic_ui_renderer, user_input  # type: ignore[import-not-found]
from .preprocessing import preprocess_options  # type: ignore[import-not-found]
from .schema_builder import build_ui_schema  # type: ignore[import-not-found]
from .dispatcher import dispatch_tokens  # type: ignore[import-not-found]


# MENU CONTROLLER & UI FLOW ORCHESTRATION ENGINE
# This utility orchestrates interactive menu flows by coordinating option preprocessing,
# UI schema generation, heuristic rendering, validated user ingress collection, and token dispatch routing.
# [>] EXECUTING MENU CONTROLLER ORCHESTRATION
def menu_controller(
    options: dict[str, Callable[..., Any]],
    title: str = "System Orchestrator",
    state: dict[str, Any] | None = None,
    critical: bool = True,
    shorthand: bool = False,
    batch: bool = False,
    template: str | None = None,
    ui_config: dict[str, Any] | None = None,
    allow_back: bool = False,
    renderer: Callable[..., str] = heuristic_ui_renderer,
) -> Any:
    """
    Orchestrates UI flow and functional execution via validated ingress.

    Args:
        options: Dictionary mapping option labels to executable callback handlers.
        title: Title string describing the menu context and UI header message.
        state: Optional state dictionary container for runtime telemetry injection.
        critical: Boolean flag controlling whether user input failure raises a critical error.
        shorthand: Boolean flag enabling multi-column shorthand grid layouts.
        batch: Boolean flag indicating whether multiple option selections are permitted.
        template: Optional custom string template for rendering menu rows.
        ui_config: Optional configuration dictionary containing custom UI layout and spatial rules.
        allow_back: Boolean flag determining whether to inject a backward navigation option.
        renderer: Callable UI rendering engine function (defaults to heuristic_ui_renderer).

    Returns:
        Any: The execution result of the selected option(s), "BACK" if navigating backward, or None if aborted.
    """
    # OPTION PREPROCESSING & INGRESS PREPARATION
    # Normalizes option definitions, extracts hotkeys or numeric indices, injects back navigation if permitted,
    # and constructs interactive prompt strings.
    working_options, entries, prompt_str, is_mnemonic = preprocess_options(
        options, title, shorthand, batch, ui_config, allow_back
    )

    if not entries:
        return None

    # UI SCHEMA CONSTRUCTION
    # Builds the structured layout schema and metadata container required by the UI renderer.
    ui_schema, _ = build_ui_schema(
        title, entries, is_mnemonic, shorthand, template, ui_config
    )

    # RENDERER ARGUMENT CONFIGURATION & SIGNATURE INSPECTION
    # Prepares rendering parameters from layout configuration and filters them
    # against the target renderer function's parameter signature.
    renderer_args: dict[str, Any] = {"schema": ui_schema, "state": state}

    if ui_config:
        if "width" in ui_config:
            renderer_args["width"] = ui_config["width"]
        if "height" in ui_config:
            renderer_args["height"] = ui_config["height"]
        if "wrap_text" in ui_config:
            renderer_args["wrap_text"] = ui_config["wrap_text"]

    renderer_sig = inspect.signature(renderer)
    filtered_renderer_args = {
        k: v for k, v in renderer_args.items() if k in renderer_sig.parameters
    }

    # TERMINAL UI RENDERING
    # Evaluates and prints the rendered user interface layout to the terminal console.
    print(renderer(**filtered_renderer_args))

    # INGRESS FIELD SPECIFICATION & TYPE CASTING
    # Configures input type casting rules and boundary constraints (choices or min/max ranges)
    # depending on whether mnemonic hotkey or numeric selection mode is active.
    cast_type = "str" if is_mnemonic else "int"
    if batch:
        cast_type = "list_str" if is_mnemonic else "list_int"

    ingress_field: dict[str, Any] = {
        "key": "selection",
        "label": prompt_str,
        "cast": cast_type,
    }

    if is_mnemonic:
        ingress_field["choices"] = [e["hotkey"] for e in entries]
    else:
        ingress_field["min"] = 1
        ingress_field["max"] = len(entries)

    # VALIDATED USER INPUT COLLECTION
    # Prompts the operator for selection input, applying validation gates and handling critical aborts.
    ingress_results = user_input(
        schema=[ingress_field],
        silent=True,
        critical=critical,
    )

    if not ingress_results:
        return None

    raw_selection: Any = ingress_results.get("selection", "")

    # TOKEN DISPATCH & EXECUTION ROUTING
    # Normalizes selected tokens, maps them to functional action vectors, and dispatches execution.
    return dispatch_tokens(
        raw_selection,
        entries,
        working_options,
        is_mnemonic,
        batch,
        state,
    )
