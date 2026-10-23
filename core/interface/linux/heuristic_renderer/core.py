import textwrap
from typing import Any

from .compositor import draw_box, draw_text  # type: ignore[import-not-found]
from .layout import resolve_layout, resolve_entries  # type: ignore[import-not-found]


# HEURISTIC GRID RENDERER & 2D ABSOLUTE CANVAS COMPOSITOR
# This function serves as the core visual synthesizer for the heuristic terminal engine,
# managing absolute coordinate mapping, opaque layer masking, custom framing, text wrapping,
# and atomic 2D grid consolidation into a final string buffer.
# [>] EXECUTING HEURISTIC GRID RENDERER & SYNTHESIS
def heuristic_grid_renderer(
    schema: dict[str, Any],
    state: dict[str, Any] | None = None,
    width: int = 80,
    height: int | str = "auto",
    wrap_text: bool = True,
) -> str:
    """
    The 'Ink' of the heuristic terminal engine (Absolute 2D Grid Compositor with Text Wrapping & Layer Flow).

    This function acts as a pure visual synthesizer with absolute coordinate
    mapping and automatic boundary text wrapping. It is decoupled from
    functional logic and session state management, focusing strictly on
    the structural mechanics of terminal canvas painting, custom framing,
    customizable borders, grid-level alignment, depth sorting, relative layout flows,
    opaque masking, and dynamic auto-height resolution.

    Args:
        schema: Configuration dictionary containing layout metadata and section definitions.
        state: Optional dictionary containing runtime state values for telemetry binding.
        width: Total width constraint for the rendered character grid canvas.
        height: Total height constraint or 'auto' dynamic sizing mode.
        wrap_text: Boolean flag determining whether long content lines should wrap within section bounds.

    Returns:
        str: The consolidated multi-line string representing the fully rendered 2D terminal buffer.
    """
    meta = schema.get("metadata", {})
    sections = schema.get("sections", [])

    # PRE-PASS: LAYOUT & BOUNDS RESOLUTION
    # Evaluates section coordinates, dimensions, and relative stacking constraints
    # to determine total required vertical space.
    resolved_sections, max_required_y = resolve_layout(sections, state, wrap_text)

    # Add space for bottom prompt if defined
    if meta.get("prompt"):
        max_required_y += 1

    # DYNAMIC CANVAS HEIGHT RESOLUTION
    # Computes the definitive canvas height constraint based on auto-sizing rules or explicit input.
    if height == "auto":
        canvas_height = max(max_required_y, 4)
    else:
        canvas_height = int(height)

    canvas_width = width

    # 2D BUFFER INITIALIZATION: CANVAS CREATION
    # Allocates the 2D character matrix filled with blank whitespace cells.
    buffer = [[" " for _ in range(canvas_width)] for _ in range(canvas_height)]

    # METADATA & BROADCAST INITIALIZATION
    # Renders top-level telemetry status messages and informational banners into the header rows.
    if meta.get("task_msg"):
        draw_text(
            1, 0, f"[~] {meta['task_msg'].upper()}", canvas_width, canvas_height, buffer
        )

    if meta.get("info_msg"):
        draw_text(1, 1, f"[i] {meta['info_msg']}", canvas_width, canvas_height, buffer)

    # SECTIONAL GRID SYNTHESIS (ABSOLUTE PLACEMENT & FLOW)
    # Iterates through each resolved section to apply opaque masking, draw structural boxes,
    # and paint wrapped text content into the active grid buffer.
    for section in resolved_sections:
        box_x = section["_box_x"]
        box_y = section["_box_y"]
        box_w = section["_box_w"]
        box_h = section["_box_h"]
        source_lines = section["_source_lines"]

        # OPAQUE MASKING / BUFFER CLEARING
        # Clears the target bounding box area with blank spaces to ensure clean layer rendering
        # and prevent visual bleeding from overlapping elements.
        for y_coord in range(box_y, box_y + box_h):
            for x_coord in range(box_x, box_x + box_w):
                if 0 <= x_coord < canvas_width and 0 <= y_coord < canvas_height:
                    buffer[y_coord][x_coord] = " "

        label = section.get("label", "")
        has_box = section.get("has_box", True)
        border_style = section.get("border_style", "")

        # BOUNDARY & PADDING CALCULATIONS BASED ON DESIGN CHOICE
        # Configures content offsets and inner widths depending on whether the section features a rendered box border.
        if has_box:
            draw_box(
                box_x,
                box_y,
                box_w,
                box_h,
                buffer,
                border_style,
                title=label,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
            )
            max_content_width = box_w - 4
            current_y_offset = 1
            max_height_limit = box_h - 1
            text_x = box_x + 2
        else:
            max_content_width = box_w
            current_y_offset = 0
            max_height_limit = box_h
            text_x = box_x

        # GRID MAPPING & TEXT WRAP EXECUTION
        # Processes line content, applying text wrapping and rendering each chunk sequentially
        # within the section's coordinate boundaries.
        for line in source_lines:
            if wrap_text and max_content_width > 0:
                wrapped_chunks = textwrap.wrap(line, width=max_content_width)
                if not wrapped_chunks:
                    wrapped_chunks = [""]
            else:
                wrapped_chunks = [line]

            for chunk in wrapped_chunks:
                if current_y_offset < max_height_limit:
                    draw_text(
                        text_x,
                        box_y + current_y_offset,
                        chunk,
                        canvas_width,
                        canvas_height,
                        buffer,
                    )
                    current_y_offset += 1

    # INGRESS PROMPT FINALIZATION: INTERACTIVE HANDOFF
    # Renders the interactive prompt string at the bottom border of the terminal canvas if specified.
    if meta.get("prompt"):
        draw_text(
            1,
            canvas_height - 1,
            meta["prompt"],
            canvas_width,
            canvas_height,
            buffer,
        )

    # BUFFER CONSOLIDATION: ATOMIC 2D GRID RENDERING
    # Flattens the 2D character matrix buffer into a single newline-delimited string payload.
    return "\n".join("".join(row) for row in buffer)


# LINEAR UI COMPOSITOR & MULTI-COLUMN SYNTHESIS ENGINE
# This utility synthesizes a linear, line-by-line terminal UI buffer supporting
# multi-column layouts, raw text blocks, and dynamic section labels. By managing
# entry delegation and column slicing, it builds structured text layouts without absolute coordinates.
# [>] EXECUTING LINEAR UI RENDERER & COLUMN SLICING
def heuristic_ui_renderer(
    schema: dict[str, Any],
    state: dict[str, Any] | None = None,
) -> str:
    """
    Synthesizes a linear, line-by-line terminal UI buffer supporting
    multi-column layouts and raw text blocks.

    Args:
        schema: Configuration dictionary containing layout metadata and section definitions.
        state: Optional dictionary containing runtime state values for telemetry binding.

    Returns:
        str: A consolidated multi-line string representing the linear text-based UI buffer.
    """
    meta = schema.get("metadata", {})
    sections = schema.get("sections", [])
    buffer: list[str] = []

    # METADATA & BROADCAST INITIALIZATION
    # Appends top-level telemetry task messages and informational banners to the primary text buffer.
    if meta.get("task_msg"):
        buffer.append(f"[~] {meta['task_msg'].upper()}")

    if meta.get("info_msg"):
        buffer.append(f"[i] {meta['info_msg']}")

    # SECTIONAL GRID SYNTHESIS & COLUMN SLICING
    # Iterates through each section definition, appending section labels and delegating
    # entry formatting to the layout helper utility.
    for _idx, section in enumerate(sections, 1):
        if section.get("label"):
            buffer.append(section["label"])

        id_type = section.get("id_type", "auto_int")
        template = section.get("row_template", "{key}. {label}: {val}")
        entries = section.get("entries", [])
        cols = section.get("cols", 1)
        is_raw_block = section.get("raw_block", False)

        # DELEGATED ENTRY RESOLUTION
        # Calls the entry resolution engine to poll state and format template strings.
        rendered_entries = resolve_entries(entries, state, id_type, template)

        # GRID MAPPING & MULTI-COLUMN DISTRIBUTION
        # Slices rendered entries into columnar chunks, joining them with horizontal spacing
        # and handling raw block indentation requirements.
        for i in range(0, len(rendered_entries), cols):
            row_slice = rendered_entries[i : i + cols]
            joined_row = "    ".join(row_slice)

            if is_raw_block:
                indented_block = "\n".join(
                    f"    {line}" for line in joined_row.splitlines()
                )
                buffer.append(indented_block)
            else:
                buffer.append(f"    {joined_row}")

    # INTERACTIVE PROMPT FINALIZATION
    # Appends the ingress command prompt string to the end of the linear buffer if defined.
    if meta.get("prompt"):
        buffer.append(meta["prompt"])

    # BUFFER CONSOLIDATION: LINEAR STRING COMPOSITION
    # Joins all accumulated buffer lines into a single newline-delimited output payload.
    return "\n".join(buffer)
