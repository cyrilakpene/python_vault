import textwrap
from collections.abc import Sequence
from typing import Any

# PREDEFINED BORDER STYLES
# Pre-configured character sets for standard box-drawing frames.
border_styles: dict[str, dict[str, str]] = {
    "single": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
    "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
    "rounded": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
    "ascii": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"},
    "heavy": {"tl": "┏", "tr": "┓", "bl": "┗", "br": "┛", "h": "━", "v": "┃"},
}


# HEURISTIC INTERFACE SYNTHESIS LAYER
# This module implements the visual construction logic for the heuristic
# engine. By separating 'Rendering' from 'Decision Logic', we
# ensure the UI can be updated or themed without impacting the state machine.
# Upgraded to support absolute 2D grid canvas composition, text wrapping,
# custom section styling, custom/configurable box borders, Z-Index layer sorting,
# relative flow stacking, opaque box masking, and dynamic "auto" canvas/box height calculation.
def heuristic_grid_renderer(
    schema: dict[str, Any],
    state: dict[str, Any] | None = None,
    width: int | str = 80,
    height: int | str = "auto",
    wrap_text: bool = True,
) -> str:
    """The 'Ink' of the heuristic terminal engine (Absolute 2D Grid Compositor with Text Wrapping & Layer Flow).

    This function acts as a pure visual synthesizer with absolute coordinate
    mapping and automatic boundary text wrapping. It is decoupled from
    functional logic and session state management, focusing strictly on
    the structural mechanics of terminal canvas painting, custom framing,
    customizable borders, grid-level alignment, depth sorting, relative layout flows,
    opaque masking, and dynamic auto-height resolution.

    Args:
        schema: A blueprint dictionary defining metadata, absolute/relative section coordinates (x, y, w, h),
            border styles, and entry formatting protocols.
        state: The transient session state; used only for data injection
            into 'Current: {val}' fields during the discovery pass.
        width: The absolute column width of the virtual terminal canvas, or "auto" to adapt to terminal size.
        height: The absolute row height of the virtual terminal canvas,
            or "auto" to dynamically compute bounds relative to the last section item.
        wrap_text: If True, automatically wraps text exceeding box/section boundaries.

    Returns:
        str: A fully compiled absolute grid visual buffer ready for terminal broadcast.
    """

    meta = schema.get("metadata", {})
    sections = schema.get("sections", [])

    # DYNAMIC CANVAS WIDTH RESOLUTION
    # Resolves column width from explicit integer inputs or default terminal fallback.
    if width == "auto":
        canvas_width = 80
    else:
        canvas_width = int(width)

    # SEQUENTIAL OVERWRITING & PRE-PASS RESOLUTION (Z-INDEX LAYER SORTING)
    # We sort sections by 'z_index' (defaulting to 0) prior to calculating dynamic dimensions and rendering.
    sorted_sections = sorted(sections, key=lambda s: s.get("z_index", 0))

    # PRE-PASS: DYNAMIC HEIGHT & RELATIVE STACKING RESOLUTION
    # Evaluates section dimensions, relative flow coordinates (stack_below), entry content line wrapping,
    # and dynamic box heights (h="auto") to compute the required maximum canvas height prior to buffer creation.
    rendered_bounds: dict[str, dict[str, int]] = {}
    resolved_sections: list[dict[str, Any]] = []
    max_required_y = 2  # Account for top metadata headers

    for section in sorted_sections:
        sec = section.copy()
        section_id = sec.get("id")
        has_box = sec.get("has_box", True)

        # MANUAL COORDINATE MANAGEMENT (RELATIVE FLOW)
        # Resolves dynamic stacking coordinates relative to previous parent bounds.
        stack_below_id = sec.get("stack_below")
        if stack_below_id and stack_below_id in rendered_bounds:
            parent = rendered_bounds[stack_below_id]
            box_x = parent["x"]
            box_y = parent["y"] + parent["h"] + 1  # 1-row gap spacing
        else:
            box_x = sec.get("x", 0)
            box_y = sec.get("y", 2)

        # RESOLUTION PROTOCOLS: ENTRY & TEMPLATE EVALUATION
        id_type = sec.get("id_type", "auto_int")
        template = sec.get("row_template", "{key}. {label}: {val}")
        entries = sec.get("entries", [])
        is_raw_block = sec.get("raw_block", False)

        rendered_lines: list[str] = []
        for i, entry in enumerate(entries):
            key = str(i + 1) if id_type == "auto_int" else entry.get("hotkey", "")
            val = ""
            if state and "state_ref" in entry:
                val = str(state.get(entry["state_ref"], "N/A"))
            rendered_lines.append(
                template.format(key=key, label=entry.get("label", ""), val=val)
            )

        source_lines: Sequence[str] = []
        if is_raw_block and entries:
            raw_content = state.get(entries[0].get("state_ref"), "") if state else ""
            source_lines = raw_content.splitlines()
        else:
            source_lines = rendered_lines

        # SECTION WIDTH RESOLUTION
        box_w = sec.get("w", 40)
        if box_w == "auto":
            max_line_len = max((len(line) for line in source_lines), default=10)
            box_w = max_line_len + (4 if has_box else 0)

        # SECTION HEIGHT RESOLUTION (h="auto" SUPPORT)
        box_h = sec.get("h", 10)
        if box_h == "auto":
            max_content_width = (box_w - 4) if has_box else box_w
            wrapped_line_count = 0
            for line in source_lines:
                if wrap_text and max_content_width > 0:
                    chunks = textwrap.wrap(line, width=max_content_width)
                    wrapped_line_count += len(chunks) if chunks else 1
                else:
                    wrapped_line_count += 1
            box_h = max(wrapped_line_count + (2 if has_box else 0), 1)

        # CACHE RESOLVED SPATIAL BOUNDS FOR DOWNSTREAM STACKING
        sec["_box_x"] = box_x
        sec["_box_y"] = box_y
        sec["_box_w"] = box_w
        sec["_box_h"] = box_h
        sec["_source_lines"] = source_lines

        if section_id:
            rendered_bounds[section_id] = {
                "x": box_x,
                "y": box_y,
                "w": box_w,
                "h": box_h,
            }

        max_required_y = max(max_required_y, box_y + box_h)
        resolved_sections.append(sec)

    # Add space for bottom prompt if defined
    if meta.get("prompt"):
        max_required_y += 1

    # DYNAMIC CANVAS HEIGHT RESOLUTION
    # Computes absolute canvas height dynamically if height="auto", or casts explicit integer bound.
    if height == "auto":
        canvas_height = max(max_required_y, 4)
    else:
        canvas_height = int(height)

    # 2D BUFFER INITIALIZATION: CANVAS CREATION
    # We initialize a fixed-size 2D character matrix buffer to allow absolute
    # (x, y) coordinate placement, enabling multi-panel cinematic dashboards.
    # [>] INITIALIZING ABSOLUTE SCREEN GRID
    buffer = [[" " for _ in range(canvas_width)] for _ in range(canvas_height)]

    # INTERNAL UTILITY: ABSOLUTE TEXT PLACEMENT
    # Safely writes a string horizontally into the 2D buffer at a specific coordinate.
    # [>] EXECUTING ABSOLUTE TEXT PLACEMENT
    def _draw_text(x: int, y: int, text: str):
        for i, char in enumerate(text):
            if 0 <= x + i < canvas_width and 0 <= y < canvas_height:
                buffer[y][x + i] = char

    # INTERNAL UTILITY: ABSOLUTE BOX FRAME COMPOSITOR
    # Draws a framed structural window with an optional title and configurable borders at precise grid bounds.
    # [>] EXECUTING BOX FRAME COMPOSITOR
    def _draw_box(
        start_x: int,
        start_y: int,
        w: int,
        h: int,
        border_style: str | dict[str, str],
        title: str = "",
    ):
        # Resolve character set from predefined name or custom character dictionary
        style: dict[str, str] = {}
        if isinstance(border_style, dict):
            style = border_style
        else:
            style = border_styles.get(border_style, border_styles["rounded"])

        tl = style.get("tl", "┌")
        tr = style.get("tr", "┐")
        bl = style.get("bl", "└")
        br = style.get("br", "┘")
        h_char = style.get("h", "─")
        v_char = style.get("v", "│")

        # Draw horizontal borders
        for x in range(start_x, start_x + w):
            if 0 <= start_y < canvas_height and 0 <= x < canvas_width:
                buffer[start_y][x] = h_char
            if 0 <= start_y + h - 1 < canvas_height and 0 <= x < canvas_width:
                buffer[start_y + h - 1][x] = h_char
        # Draw vertical borders
        for y in range(start_y, start_y + h):
            if 0 <= y < canvas_height and 0 <= start_x < canvas_width:
                buffer[y][start_x] = v_char
            if 0 <= y < canvas_height and 0 <= start_x + w - 1 < canvas_width:
                buffer[y][start_x + w - 1] = v_char
        # Draw corners
        if 0 <= start_y < canvas_height and 0 <= start_x < canvas_width:
            buffer[start_y][start_x] = tl
        if 0 <= start_y < canvas_height and 0 <= start_x + w - 1 < canvas_width:
            buffer[start_y][start_x + w - 1] = tr
        if 0 <= start_y + h - 1 < canvas_height and 0 <= start_x < canvas_width:
            buffer[start_y + h - 1][start_x] = bl
        if 0 <= start_y + h - 1 < canvas_height and 0 <= start_x + w - 1 < canvas_width:
            buffer[start_y + h - 1][start_x + w - 1] = br
        # Draw optional title tag
        if title:
            _draw_text(start_x + 2, start_y, f"[{title}]")

    # METADATA & BROADCAST INITIALIZATION
    # We extract high-level messaging from the schema to set the context.
    # [>] INITIALIZING METADATA HEADERS
    if meta.get("task_msg"):
        _draw_text(1, 0, f"[~] {meta['task_msg'].upper()}")

    # INFO BROADCAST: CONTEXTUAL DISCOVERY
    # We inject the secondary status message below the task header.
    # [>] EXECUTING INFO SUB-HEADER DRAW
    if meta.get("info_msg"):
        _draw_text(1, 1, f"[i] {meta['info_msg']}")

    # SECTIONAL GRID SYNTHESIS (ABSOLUTE PLACEMENT & FLOW)
    # We iterate through the pre-resolved sections, painting custom frames and content onto the canvas matrix.
    for section in resolved_sections:
        box_x = section["_box_x"]
        box_y = section["_box_y"]
        box_w = section["_box_w"]
        box_h = section["_box_h"]
        source_lines = section["_source_lines"]

        # OPAQUE MASKING / BUFFER CLEARING
        # Clears the exact rectangular footprint of the section prior to rendering.
        # This guarantees that foreground overlays/popups completely mask out any
        # underlying background text and prevent text bleed past borders.
        # [>] EXECUTING OPAQUE RECTANGLE CLEAR
        for y_coord in range(box_y, box_y + box_h):
            for x_coord in range(box_x, box_x + box_w):
                if 0 <= x_coord < canvas_width and 0 <= y_coord < canvas_height:
                    buffer[y_coord][x_coord] = " "

        label = section.get("label", "")

        # DESIGN CUSTOMIZATION: CONFIGURABLE SECTION BORDER SWITCH & STYLING
        # Allows users to choose their layout design (framed box vs clean text canvas) and custom border characters.
        has_box = section.get("has_box", True)
        border_style = section.get("border_style", "")

        # BOUNDARY & PADDING CALCULATIONS BASED ON DESIGN CHOICE
        if has_box:
            _draw_box(
                box_x,
                box_y,
                box_w,
                box_h,
                title=label,
                border_style=border_style,
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
        # If text wrapping is enabled, overflowing strings are broken down into chunks
        # and cleanly distributed across multiple rows within the section height limits.
        # [>] EXECUTING TEXT WRAP AND GRID COMPOSITION
        for line in source_lines:
            if wrap_text and max_content_width > 0:
                wrapped_chunks = textwrap.wrap(line, width=max_content_width)
                if not wrapped_chunks:
                    wrapped_chunks = [""]
            else:
                wrapped_chunks = [line]

            for chunk in wrapped_chunks:
                if current_y_offset < max_height_limit:
                    _draw_text(text_x, box_y + current_y_offset, chunk)
                    current_y_offset += 1

    # INGRESS PROMPT FINALIZATION: INTERACTIVE HANDOFF
    # We append the user interaction prompt near the bottom of the canvas grid.
    # [>] FINALIZING INGRESS GATE
    if meta.get("prompt"):
        _draw_text(1, canvas_height - 1, meta["prompt"])

    # BUFFER CONSOLIDATION: ATOMIC 2D GRID RENDERING
    # We collapse the 2D character matrix into a single newline-delimited string.
    # [>] EXECUTING TERMINAL IMAGE EXPORT
    return "\n".join("".join(row) for row in buffer)


# LIVE TELEMETRY WRAPPER LAYER
# This module implements the ANSI control mechanics for real-time terminal refreshing.
# By combining absolute canvas compilation with line-purge escape sequences and cursor
# homing, it enables flicker-free, in-place telemetry updates without text bleeding.
def render_live_frame(
    schema: dict[str, Any],
    state: dict[str, Any] | None = None,
    width: int | str = 80,
    height: int | str = "auto",
    clear_below: int = 0,
) -> str:
    """The live telemetry transmission wrapper for the heuristic grid engine.

    This function wraps the absolute grid output with ANSI control sequences
    designed specifically for real-time, in-place terminal updates. It manages
    line-clearing artifacts and cursor positioning to ensure fluid rendering,
    with optional line padding to clear out trailing input prompt artifacts.

    Args:
        schema: A blueprint dictionary defining layout metadata and sections.
        state: The transient session state for live data injection.
        width: The absolute column width of the virtual terminal canvas, or "auto" to adapt to terminal size.
        height: The absolute row height of the virtual terminal canvas,
            or "auto" to dynamically compute bounds relative to the last section item.
        clear_below: Number of extra lines below the canvas to forcefully clear and pad,
            preventing ghost artifacts from external input prompts.

    Returns:
        str: An ANSI-escaped frame string ready for flicker-free live broadcast.
    """

    # GRID COMPOSITION PASS: FRAME GENERATION
    # We invoke the underlying absolute 2D grid compositor to render the core visual
    # layout buffer based on the provided schema and real-time state telemetry.
    # [>] EXECUTING GRID COMPOSITOR SYNTHESIS
    raw_output = heuristic_grid_renderer(schema, state, width=width, height=height)

    # ANSI LINE PURGING: GHOST ARTIFACT ERADICATION
    # We iterate through each line of the raw buffer and append the 'Erase in Line' (\033[K)
    # escape sequence. This guarantees that any lingering characters from a longer
    # previous frame are completely wiped out from the terminal's right edge.
    # [>] INJECTING LINE CLEAR ESCAPE CODES
    cleaned_lines = [line + "\033[K" for line in raw_output.splitlines()]

    # BUFFER PADDING & SUB-CANVAS CLEARING
    # If a clear_below boundary is defined, we append targeted blank rows with
    # line-purge codes. This surgically wipes out trailing input lines left by
    # external ingress mechanisms (like user_input) without over-clearing the terminal.
    # [>] EXECUTING SUB-CANVAS LINE CLEARANCE
    if clear_below > 0:
        canvas_w = 80 if width == "auto" else int(width)
        for _ in range(clear_below):
            cleaned_lines.append(" " * canvas_w + "\033[K")

    # BUFFER CONSOLIDATION: CURSOR HOMING & BROADCAST
    # We prepend the ANSI 'Cursor Home' (\033[H) sequence to the joined buffer.
    # This repositions the cursor to the top-left corner (0,0) of the terminal screen,
    # allowing the new frame to cleanly overwrite the old one in place.
    # [>] FINALIZING LIVE FRAME EXPORT
    return "\033[H" + "\n".join(cleaned_lines)
