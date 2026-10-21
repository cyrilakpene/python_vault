import inspect
from typing import Any, Callable

from interface.report_status import report_status  # type: ignore[import-not-found]
from interface.user_input import user_input  # type: ignore[import-not-found]
from interface.heuristic_ui_renderer import heuristic_ui_renderer  # type: ignore[import-not-found]
from security.runtime_context import log_path  # type: ignore[import-not-found]


# ARCHITECTURAL ORCHESTRATOR: DYNAMIC DISPATCH ENGINE
# This engine serves as the "Primary Navigation Hub" for the interface.
# By decoupling the UI rendering (Menu) from the functional dispatch
# (Logic), it ensures that the application's flow remains modular,
# state-aware, and resilient to signature mismatches.
# The engine acts as a "State-Aware Valve," ensuring that user ingress
# is strictly validated before being routed to downstream functional
# logic stations. This prevents "Dead-End" execution and ensures that
# the global state remains synchronized with user intent.
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

    This engine manages the lifecycle of operator interaction, pivoting
    between heuristic rendering and functional resolution. It implements
    strict validation protocols to ensure that all symbolic ingress
    accurately maps to the underlying logic vectors.

    Supports Universal Batching. Allows multiple selections (1, 2, 3)
    in both Shorthand (Grid) and Traditional (Vertical) UI modes.

    The 'ui_config' override layer allows for total structural customization,
    enabling the operator to define column counts, id_types, canvas bounds
    (x, y, w, h), border styles, and templates independently of the shorthand toggle.

    Args:
        options: A mapping of symbolic keys to resolution vectors (lambdas).
        title: The primary objective header for the visual buffer.
        state: Real-time telemetry for 'Current: {val}' interpolation.
        critical: If True, the controller loops until a valid selection is made.
        shorthand: Toggle for high-density mnemonic display modes (Grid).
        batch: Enables multi-selection (returns a list of resolved values).
        template: The visual blueprint for individual row construction.
        ui_config: Optional override dictionary for manual UI blueprinting
                   (e.g., {'cols': 3, 'id_type': 'auto_int', 'w': 80, 'h': 24}).
        allow_back: If True, dynamically appends a "Go Back" option (or mnemonic
                    "[b]ack") to the end of the menu entries list, returning a
                    sentinel string "BACK" on invocation to allow parent loop unwinding.
        renderer: The callable synthesis function responsible for rendering the
                  visual buffer (defaults to heuristic_ui_renderer, pluggable
                  with heuristic_grid_renderer).

    Returns:
        Any: The resolved value(s) from the selected option(s), or "BACK" if the
             dynamic exit vector was executed.
    """

    # INGRESS VALIDATION: THE INTEGRITY GATE
    # We perform a defensive check to ensure the options mapping is not
    # empty. If a null-set is detected, we abort the ingress to prevent
    # downstream logic failures or empty UI renders.
    # [>] EXECUTING NULL-SET VERIFICATION
    if not options:
        report_status(
            state="warn",
            message=f"Ingress aborted: Null-set detected for {title!r}.",
            silent=True,
            log_path=log_path,
        )
        return None

    # DYNAMIC ESCAPE LAYER: BACKWARD NAVIGATION & COGNITIVE MODE RESOLUTION
    # We clone the options dictionary to prevent mutation side-effects, and
    # resolve the mnemonic state early so we can dynamically formulate our
    # backward navigation target in the correct style.
    # [>] INITIALIZING WORK COPY AND BACKWARD COGNATES
    working_options = dict(options)
    is_mnemonic = shorthand or (ui_config and ui_config.get("id_type") == "mnemonic")

    if allow_back:
        back_label = "[b]ack" if is_mnemonic else "Go Back"
        working_options[back_label] = lambda: "__BACK__"

    # ARCHITECTURAL MAPPING & DATA PRE-DISCOVERY
    # We transform the symbolic keys from our expanded working options map into
    # a structured list of entries. This phase acts as the 'Primary Source of Truth,'
    # bridging the gap between the raw functional dispatch map and the
    # visual requirements of the UI renderer.
    # [>] INITIALIZING ENTRY BLUEPRINT
    options_labels: list[str] = list(working_options.keys())
    entries: list[dict[str, Any]] = []

    # LINGUISTIC PRE-PROCESSING: ACRONYM DISCOVERY
    # We extract the acronym mapping layer from ui_config. This ensures the
    # controller remains domain-agnostic while supporting high-fidelity
    # technical casing for terminal broadcast.
    # [>] INITIALIZING LINGUISTIC MAP
    acronym_map: dict[str, str] = (ui_config or {}).get("acronyms", {})

    # MNEMONIC RESOLUTION & ENTRY CONSTRUCTION
    # We iterate through the raw option labels to synthesize interactive
    # entries. This phase resolves how the operator will trigger specific
    # logic vectors, synchronizing extraction protocols with the intended
    # UI layout—whether triggered by shorthand defaults or config overrides.
    # [>] EXECUTING SYMBOLIC KEY DISCOVERY
    for label in options_labels:
        hotkey = ""

        # SHORTHAND PROTOCOL: MNEMONIC EXTRACTION
        # We attempt to isolate a hotkey defined within brackets (e.g., [E]xtract).
        # This extraction triggers if shorthand mode is active or if the
        # operator has manually specified a mnemonic id_type in ui_config.
        # [>] RESOLVING HOTKEY COORDINATES
        working_label = label
        if is_mnemonic:
            # We extract the mnemonic from the ORIGINAL label to ensure
            # functional mapping remains synchronized with the dispatch key.
            if "[" in label and "]" in label:
                hotkey = label.split("[")[1].split("]")[0]
                # We strip the mnemonic notation from the working label to
                # ensure the Casing Gate processes a clean alphanumeric string.
                working_label = label.replace(f"[{hotkey}]", hotkey)
            else:
                hotkey = label

        # LINGUISTIC SANITIZATION: THE CASING GATE
        # We perform a surgical transformation of the raw key. We pivot the
        # casing strategy based on the interaction mode: Mnemonic paths
        # maintain a lowercase technical aesthetic, while Ordinal paths
        # utilize Title-Casing for high-fidelity categorization.
        # [>] SYNTHESIZING HIGH-FIDELITY LABEL
        if is_mnemonic:
            # Maintain raw casing for shorthand overrides
            display_label = working_label.replace("_", " ")
        else:
            # Apply Title-Casing for standard ordinal lists
            display_label = working_label.replace("_", " ").title()

        if acronym_map:
            display_label = " ".join(
                acronym_map.get(word, word) for word in display_label.split()
            )

        # ENTRY ASSEMBLY: DATA NORMALIZATION
        # We construct the final entry object, utilizing the high-fidelity
        # display_label for visual output. We have already stripped bracket
        # notation to finalize the aesthetic while maintaining the raw
        # 'action_key' as the immutable functional coordinate. This ensures
        # 'state_ref' and 'label' remain synchronized with the resolved
        # mnemonic status.
        # [>] COMMITTING ENTRY TO SCHEMATICS
        entries.append(
            {
                "label": display_label,
                "hotkey": hotkey,
                "action_key": label,
                "state_ref": hotkey if is_mnemonic else label,
            }
        )

    # UI SYNTHESIS & PROMPT ENGINEERING
    # We generate dynamic hint tokens to guide the operator's input format.
    # By calculating the total range and sampling available keys, we provide
    # a contextual 'template' that reflects the actual operational mode,
    # ensuring hints align with the resolved mnemonic or ordinal state.
    # [>] SYNTHESIZING INTERACTION HINTS
    total_entries = len(entries)
    range_hint = f"1-{total_entries}" if total_entries > 1 else "1"

    # We pivot the example tokens based on the batching flag to ensure the
    # hint accurately represents single vs. multi-select capability.
    # The logic now respects the resolved 'is_mnemonic' status.
    if is_mnemonic:
        example_hint = (
            ", ".join([e["hotkey"] for e in entries[:2]])
            if batch and total_entries > 1
            else (entries[0]["hotkey"] if entries else "key")
        )
    else:
        example_hint = "1, 2" if batch and total_entries > 1 else "1"

    # INGRESS STRING CONSTRUCTION: THE OPERATOR SIGNAL
    # We pivot the prompt text based on the resolved mnemonic status and
    # batch flags. This ensures the terminal nomenclature matches the
    # visual layout and interaction constraints, signaling 'Override'
    # for mnemonics vs 'Select' for ordinal lists.
    # [>] FINALIZING PROMPT SPECIFICATION
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

    # HEURISTIC TEMPLATE SELECTION: VISUAL PROTOTYPING
    # We resolve the visual blueprint for the rows by checking the override
    # layers in order of precedence: ui_config, the explicit template arg,
    # or a heuristic default based on the resolved mnemonic state.
    # [>] RESOLVING ROW BLUEPRINT
    if not template:
        # First, check if ui_config explicitly defined a template
        template = (ui_config or {}).get("row_template")

        # If still null, pivot defaults based on mnemonic status
        if not template:
            template = "[{key}] {label:<16}" if is_mnemonic else "{key:<2}. {label}"

    # UI SCHEMA CONFIGURATION: THE ARCHITECTURAL SPEC
    # We assemble the final schema for the heuristic renderer. This phase
    # consolidates metadata, sectional protocols, and the entry list into
    # a unified architectural blueprint. By merging the 'ui_config' layer
    # with the resolved defaults, we enable full structural override of
    # columns, id_types, templates, and spatial coordinates without breaking
    # the functional gate.
    # [>] SYNTHESIZING UI BLUEPRINT

    # Define the resolved default layer
    layout_defaults: dict[str, Any] = {
        "id_type": "mnemonic" if is_mnemonic else "auto_int",
        "cols": 2 if shorthand else 1,
        "row_template": template,
    }

    # Execute the merge: ui_config values supersede defaults
    # This enables patterns like shorthand=False but cols=2 or custom coordinates.
    if ui_config:
        layout_defaults.update(ui_config)

    # Construct primary section specification
    section_spec: dict[str, Any] = {
        "id_type": layout_defaults["id_type"],
        "cols": layout_defaults["cols"],
        "row_template": layout_defaults["row_template"],
        "entries": entries,
    }

    # SPATIAL & STYLING INJECTION FOR 2D GRID RENDERER
    # We forward grid-specific spatial properties (x, y, w, h, border_style, etc.)
    # from layout_defaults into the section payload if present[span_2](start_span)[span_2](end_span).
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

    ui_schema: dict[str, Any] = {
        "metadata": {
            "task_msg": title,
            "prompt": None,
        },
        "sections": [section_spec],
    }

    # UI RENDERING: DELEGATED PAINTING & DYNAMIC DISPATCH
    # We interrogate the target renderer's signature to inject supported arguments
    # (such as schema, state, width, and height) dynamically[span_3](start_span)[span_3](end_span)[span_4](start_span)[span_4](end_span).
    # [>] EXECUTING TERMINAL BROADCAST
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

    print(renderer(**filtered_renderer_args))

    # INGRESS CAPTURE: OPERATOR FEEDBACK
    # We determine the appropriate data casting protocol based on the
    # resolved mnemonic status and batching status. This ensures that
    # user input is normalized before reaching the resolution gate,
    # preventing type-mismatch failures when UI overrides are active.
    # [>] WAITING FOR OPERATOR INGRESS
    cast_type = "str" if is_mnemonic else "int"
    if batch:
        cast_type = "list_str" if is_mnemonic else "list_int"

    # INGRESS SCHEMA SYNTHESIS: THE VALIDATION BLUEPRINT
    # We dynamically construct the field schema to ensure the 'Gatekeeper'
    # (user_input) has the necessary boundaries to enforce integrity.
    # By pivoting between 'min/max' for ordinals and 'choices' for
    # mnemonics based on the resolved mode, we prevent out-of-bounds
    # ingress from ever reaching the resolution gate.
    # [>] CONSTRUCTING INGRESS FIELD
    ingress_field: dict[str, Any] = {
        "key": "selection",
        "label": prompt_str,
        "cast": cast_type,
    }

    if is_mnemonic:
        # In Mnemonic mode, we restrict ingress to the defined hotkeys.
        ingress_field["choices"] = [e["hotkey"] for e in entries]
    else:
        # In Traditional mode, we enforce numeric boundaries (1 to N).
        ingress_field["min"] = 1
        ingress_field["max"] = len(options_labels)

    # INGRESS EXECUTION: THE INPUT GATE
    # We utilize the 'user_input' interface to capture the operator's
    # selection. The 'critical' flag determines if the system should
    # force a valid response before proceeding. By passing our dynamic
    # schema, we delegate the 'Retry-Until-Valid' logic to the gatekeeper.
    # [>] EXECUTING DATA INGRESS
    ingress_results = user_input(
        schema=[ingress_field],
        silent=True,
        critical=critical,
    )

    # DEFENSIVE EXIT: NULL RESOLUTION
    # If the ingress fails or the operator cancels the action, we return
    # None to prevent downstream functional dispatch.
    # [>] EVALUATING INGRESS INTEGRITY
    if not ingress_results:
        return None

    # RESOLUTION GATE: COORDINATE MAPPING
    # We retrieve the raw selection from the ingress results. This value
    # represents the operator's symbolic intent, which must now be
    # mapped back to the original functional vectors.
    # [>] INITIALIZING RESOLUTION PIPELINE
    raw_selection: Any = ingress_results.get("selection", "")

    # BATCH TOKENIZATION: DATA NORMALIZATION
    # We ensure that all ingress—whether single or batch—is converted
    # into a standardized list of sanitized strings. By normalizing to
    # lowercase and stripping whitespace, we ensure the coordinate lookup
    # remains resilient to variations in operator input.
    # [>] EXECUTING INPUT SANITIZATION
    tokens = (
        [str(t).lower().strip() for t in raw_selection]  # type: ignore[arg-type]
        if isinstance(raw_selection, list)
        else [str(raw_selection).lower().strip()]
    )

    # RESULT AGGREGATION: THE COLLECTION RESERVOIR
    # We initialize a reservoir to hold the resolved values. This
    # allows the orchestrator to support both singular and multi-select
    # returns within the same logic stream.
    # [>] PREPARING RESULT BUFFER
    selected_results: list[Any] = []

    # FUNCTIONAL DISPATCH: COORDINATE RESOLUTION
    # We iterate through the sanitized tokens to resolve the operator's
    # specific intent. This phase performs the critical mapping between
    # the terminal symbol (token) and the underlying functional index,
    # ensuring the lookup protocol matches the resolved UI mode.
    # [>] EXECUTING TOKEN RESOLUTION LOOP
    for selection_str in tokens:
        idx: int = -1

        if is_mnemonic:
            # RESOLUTION: HOTKEY MAPPING
            # In mnemonic mode, we perform a symbolic search across the
            # entry list to find a matching hotkey. We use case-insensitive
            # comparison to ensure operator flexibility.
            # [>] SCANNING MNEMONIC COORDINATES
            idx = next(
                (
                    i
                    for i, e in enumerate(entries)
                    if e["hotkey"].lower() == selection_str
                ),
                -1,
            )
        else:
            # RESOLUTION: ORDINAL INDEX MAPPING
            # In traditional (non-mnemonic) mode, we convert the ordinal
            # string back into a zero-based integer index. We wrap this
            # in a defensive block to catch any malformed numeric ingress
            # that bypassed the gatekeeper.
            # [>] CALCULATING ORDINAL OFFSET
            try:
                idx = int(selection_str) - 1
            except (ValueError, TypeError):
                idx = -1

        # DISPATCH HUB: BOUNDARY CHECK & EXECUTION
        # Before triggering a logic vector, we perform a boundary check
        # against the options map. This ensures that only valid,
        # authenticated indices proceed to the execution pipeline.
        # [>] EXECUTING BOUNDARY VERIFICATION
        if 0 <= idx < len(entries):
            # We resolve the action_key from the entries list. This is
            # more robust than indexing options_labels directly, as it
            # maintains the link to the original functional key defined
            # during the assembly phase.
            target_entry = entries[idx]
            target_label = target_entry["action_key"]

            # NOTE: Swapped from 'options' to 'working_options' to support
            # resolving the dynamically injected back-navigation vector!
            target_func: Callable[..., Any] = working_options[target_label]

            # REFINED SIGNATURE INSPECTION: INTROSPECTIVE DISPATCH
            # We interrogate the target function's signature to determine its
            # dependency requirements. This allows the orchestrator to
            # dynamically pivot between state-aware and pure functions.
            # [>] ANALYZING FUNCTION SIGNATURE
            sig: inspect.Signature = inspect.signature(target_func)
            params = list(sig.parameters.values())

            # REFINED DEPENDENCY RESOLUTION: STATE PROXY CHECK
            # We only inject state if the function explicitly asks for 'state'
            # or uses a dictionary type hint. Lambdas and pure functions
            # are excluded by default to prevent signature mismatches.
            # [>] EVALUATING INJECTION REQUIREMENTS
            wants_state: bool = any(
                p.name == "state"
                or (p.annotation is dict or "dict" in str(p.annotation).lower())
                for p in params
            )

            # DISPATCH: EXECUTION PIPELINE
            # The final trigger event. We inject the telemetry state if the
            # signature is 'state-seeking'; otherwise, we execute a pure
            # call. Results are staged in the reservoir for aggregation.
            # [>] TRIGGERING LOGIC VECTOR
            if wants_state and params:
                # Targeted Injection: The function has parameters and
                # has been flagged as state-seeking.
                active_state = state if state is not None else {}
                selected_results.append(target_func(active_state))
            else:
                # Pure Execution: The function is either a lambda () or
                # does not request state telemetry.
                selected_results.append(target_func())
        else:
            # DEFENSIVE ROUTING: BOUNDARY BREACH
            # If the resolved index falls outside the valid range, we trigger
            # a failure report. This informs the operator of the specific
            # routing error without crashing the dispatch loop.
            # [>] EXECUTING ERROR LOGGING
            report_status(
                state="fail",
                message=f"Routing error: Choice {selection_str!r} out of bounds.",
                log_path=log_path,
            )

    # ORCHESTRATION FINALIZATION: AGGREGATION PIVOT
    # We collapse the reservoir based on the batching flag. This ensures
    # the return signature remains predictable, providing either a
    # collection of resolved vectors or a singular atomic result.
    # [>] RELEASING CONTROL TO CALLER
    resolved_output = (
        selected_results
        if batch
        else (selected_results[0] if selected_results else None)
    )

    # UNWIND INTERCEPTION: BACK NAVIGATION SIGNAL
    # If the output matches our sentinel string from the back-nav lambda,
    # we intercept it and return a clean "BACK" command to break parent loops.
    if resolved_output == "__BACK__":
        return "BACK"

    return resolved_output


# ROUTING DISPATCH: PERSISTENT INTERACTIVE MENU LIFECYCLE
# This operational routing engine encapsulates low-level menu navigation loops.
# It manages persistent UI interaction states, intercepting backward-navigation
# sentinels to cleanly unwind frame stacks and propagate escape coordinates across
# nested terminal trees.
def menu_router(
    options: (
        dict[str, Callable[..., Any]] | Callable[[], dict[str, Callable[..., Any]]]
    ),
    is_main_menu: bool = False,
    returns_value: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Manages persistent state routing and lifecycle loops for nested sub-menus.

    This routing engine wraps the low-level 'menu_controller', providing an
    infinite execution loop that keeps the interface alive during operator
    interaction. It intercepts the backward-navigation sentinel ('BACK')
    to cleanly unwind the call stack and return control to the parent loop.

    By encapsulating the loop boilerplates, this router allows complex nested
    terminal trees to be declared as lightweight, readable configuration maps
    or evaluated dynamically via factory functions.

    Args:
        options: A mapping of symbolic keys to resolution vectors, OR a parameterless
                 callable factory returning such a mapping on every turn.
        is_main_menu: If True, disables back navigation defaults and bubble up
                        exit/termination signals.
        returns_value: If True, exits the loop immediately after executing an action
                        and returns its result to the caller.
        **kwargs: Arbitrary keyword arguments forwarded directly to the
                    underlying 'menu_controller' (e.g., title, shorthand, ui_config,
                    renderer).
    """
    # BOUNDARY DEFAULTS: NAVIGATION PATTERN ENFORCEMENT
    # We enforce backward navigation as the baseline structural default for sub-menus.
    # Unless the menu is designated as the primary interface node, we set default
    # back-navigation permissions within the parameter payload.
    if not is_main_menu:
        kwargs.setdefault("allow_back", True)

    # LIFECYCLE LOOP: PERSISTENT OPERATOR INTERACTION
    # We maintain a continuous execution loop to hold the interface state alive.
    # This prevents control from leaking back to the calling frame until an explicit
    # escape sequence or exit command is triggered by the operator.
    while True:
        # DYNAMIC EVALUATION: Evaluate callable option factory on each loop iteration
        resolved_options = options() if callable(options) else options

        result = menu_controller(resolved_options, **kwargs)

        # INTERCEPTION GATEWAY: BACKWARD ESCAPE DETECTION
        # If the controller returns the designated back-navigation sentinel,
        # we break the local loop to cleanly unwind the execution stack back
        # to the parent interface node.
        if result == "BACK":
            break

        # TERMINATION SWEEP: ROOT MENU EXIT DISPATCH
        # If operating within the primary menu frame and an explicit termination
        # signal is intercepted, we terminate the root lifecycle loop.
        if is_main_menu and result == "EXIT":
            break

        # STATE PROPAGATION: IMMEDIATE VALUE RETURN
        # When configured for value-returning workflows, we immediately yield
        # the action execution payload directly to the upstream caller.
        if returns_value and result is not None:
            return result
