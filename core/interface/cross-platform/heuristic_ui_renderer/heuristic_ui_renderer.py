from typing import Any

from interface.report_status import report_status  # type: ignore[import-not-found]
from security.runtime_context import log_path  # type: ignore[import-not-found]


# HEURISTIC INTERFACE SYNTHESIS LAYER
# This module implements the visual construction logic for the heuristic
# engine. By separating the 'Rendering' from the 'Decision Logic', we
# ensure that the UI can be updated or themed without impacting the
# underlying state machine.
def heuristic_ui_renderer(
    schema: dict[str, Any], state: dict[str, Any] | None = None
) -> str:
    """
    The 'Ink' of the heuristic terminal engine.

    This function acts as a pure visual synthesizer. It is decoupled from
    functional logic and session state management, focusing strictly on
    the structural mechanics of terminal painting, grid alignment, and
    aesthetic prefixing ([!], [i], [>]).

    Args:
        schema: A blueprint dictionary defining metadata, section labels,
                and entry formatting protocols.
        state: The transient session state; used only for data injection
               into 'Current: {val}' fields during the discovery pass.

    Returns:
        str: A fully compiled visual buffer ready for terminal broadcast.
    """
    report_status(
        state="task",
        message="Initializing UI synthesis pass.",
        silent=True,
        log_path=log_path,
    )

    # METADATA & BROADCAST INITIALIZATION
    # We extract high-level messaging from the schema to set the context.
    # This phase establishes the 'Task' and 'Info' headers that define
    # the operational environment for the operator.
    # [>] INITIALIZING VISUAL BUFFER
    meta = schema.get("metadata", {})
    sections = schema.get("sections", [])
    buffer: list[str] = []

    # TASK BROADCAST: PRIMARY OBJECTIVE
    # We render the primary task message in uppercase to establish it as
    # the structural anchor. This provides the operator with immediate
    # locational awareness of the current operational goal.
    # [>] EXECUTING TASK HEADER DRAW
    if meta.get("task_msg"):
        task_str: str = meta.get("task_msg").upper()
        report_status(
            state="info",
            message=f"Rendering task header: {task_str}",
            silent=True,
            log_path=log_path,
        )
        buffer.append(f"[~] {meta['task_msg'].upper()}")

    # INFO BROADCAST: CONTEXTUAL DISCOVERY
    # We inject the secondary status message to provide transient context,
    # such as the identification of the active session or a sub-state.
    # [>] EXECUTING INFO SUB-HEADER DRAW
    if meta.get("info_msg"):
        report_status(
            state="info",
            message=f"Rendering info message: {meta['info_msg']}",
            silent=True,
            log_path=log_path,
        )
        buffer.append(f"[i] {meta['info_msg']}")

    # SECTIONAL GRID SYNTHESIS
    # We iterate through the defined sections to build the menu body.
    # This modular architecture allows for mixed-logic UIs where static
    # info blocks can precede interactive tuning vectors.
    report_status(
        state="proc",
        message=f"Synthesizing {len(sections)} layout sections...",
        silent=True,
        log_path=log_path,
    )
    for idx, section in enumerate(sections, 1):
        label: str = section.get("label", f"Section_{idx}")
        report_status(
            state="info",
            message=f"Processing section: {label!r}",
            silent=True,
            log_path=log_path,
        )

        # BOUNDARY MARKER: CATEGORICAL SEPARATION
        # We render the section label as a structural divider. This ensures
        # that in multi-category menus, the operator can visually distinguish
        # between different logical groups of data or controls.
        # [>] EXECUTING SECTION LABEL DRAW
        if section.get("label"):
            buffer.append(f"{section['label']}")

        # RESOLUTION PROTOCOLS: INTERACTION SCHEMATICS
        # We pivot between 'auto_int' (ordinal) and 'mnemonic' (hotkey)
        # to define how the operator interacts with the specific section.
        # The template acts as the visual blueprint for row construction.
        # [>] INITIALIZING SECTION PARAMETERS
        id_type = section.get("id_type", "auto_int")
        template = section.get("row_template")
        entries = section.get("entries", [])
        cols = section.get("cols", 1)
        is_raw_block = section.get("raw_block", False)

        # CELL SYNTHESIS: DYNAMIC ROW GENERATION
        # Each entry is interrogated for state references to ensure the
        # UI reflects real-time session telemetry. By mapping local keys to
        # global state, we maintain a reactive terminal interface.
        # [>] RESOLVING ENTRY COORDINATES AND STATE INJECTION
        rendered_entries: list[str] = []
        for i, entry in enumerate(entries):

            # ID RESOLUTION: INTERACTION MAPPING
            # We pivot between auto-increment (ordinal) and mnemonic hotkeys
            # to determine the operator's primary interaction vector for this cell.
            # [>] ASSIGNING COORDINATE KEY
            key = str(i + 1) if id_type == "auto_int" else entry.get("hotkey", "")

            # STATE INTERROGATION: TELEMETRY INJECTION
            # This logic bridges the gap between static templates and dynamic
            # session data. If a 'state_ref' exists, we pull the live value;
            # otherwise, we default to 'N/A' to maintain visual consistency.
            # [>] POLLING SESSION STATE
            val = ""
            if state and "state_ref" in entry:
                val = str(state.get(entry["state_ref"], "N/A"))

            # CELL CONSTRUCTION: BLUEPRINT EXECUTION
            # We finalize the individual cell string by injecting the key,
            # label, and value into the section's row template.
            # [>] RENDERING INDIVIDUAL CELL
            rendered_entries.append(
                template.format(key=key, label=entry.get("label", ""), val=val)
            )
        report_status(
            state="info",
            message=f"Rendered {len(rendered_entries)} cells for section {label!r} across {cols} column(s).",
            silent=True,
            log_path=log_path,
        )

        # GRID MAPPING: ARCHITECTURAL ALIGNMENT
        # This stage ensures visual stability by calculating column distribution.
        # By slicing the rendered entries, we prevent 'jitter' when rendering
        # high-density dashboards or mixed-width labels.
        # [>] EXECUTING GRID LAYOUT CALCULATIONS
        for i in range(0, len(rendered_entries), cols):
            # We extract a horizontal slice of cells based on the column count.
            row_slice = rendered_entries[i : i + cols]

            # THE FINAL DRAW: We join cells with architectural padding to ensure
            # horizontal alignment across the visual buffer.
            # [>] COMMITTING ROW TO BUFFER
            joined_row = "    ".join(row_slice)

            if is_raw_block:
                # Splitting by newline guarantees every line of a multi-line block
                # (like tabular data) receives the 4-space architectural prefix.
                indented_block = "\n".join(
                    f"    {line}" for line in joined_row.splitlines()
                )
                buffer.append(indented_block)
            else:
                buffer.append(f"    {joined_row}")

    # INGRESS PROMPT FINALIZATION: INTERACTIVE HANDOFF
    # We append the user interaction prompt to the end of the buffer. This
    # visual signal closes the render circuit and informs the operator
    # that the system is now idling for input or command execution.
    # [>] FINALIZING INGRESS GATE
    if meta.get("prompt"):
        report_status(
            state="info",
            message=f"Appending input prompt: {meta['prompt']}",
            silent=True,
            log_path=log_path,
        )
        buffer.append(f"{meta['prompt']}")

    report_status(
        state="done",
        message="UI buffer synthesis complete.",
        silent=True,
        log_path=log_path,
    )

    # BUFFER CONSOLIDATION: ATOMIC UI RENDERING
    # We collapse the buffer list into a single newline-delimited string.
    # This prevents fragmented terminal output and ensures a "Clean
    # Refresh" during high-frequency telemetry updates.
    # [>] EXECUTING TERMINAL IMAGE EXPORT
    return "\n".join(buffer)
