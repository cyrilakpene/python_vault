import textwrap
from collections.abc import Sequence
from typing import Any


# LAYOUT RESOLUTION & SPATIAL CALCULATION ENGINE
# This utility manages spatial arrangement, z-index layering, and dynamic bounding box metrics
# for UI sections. By evaluating relative stacking hierarchies, automatic width/height adjustments,
# and text wrapping constraints, it prepares structured layout manifests for rendering.
# [>] EXECUTING LAYOUT RESOLUTION & SPATIAL COMPOSITION
def resolve_layout(
    sections: list[dict[str, Any]],
    state: dict[str, Any] | None,
    wrap_text: bool,
) -> tuple[list[dict[str, Any]], int]:
    """
    Sorts sections by z-index and calculates dynamic box coordinates, width, height, and stacking bounds.

    Args:
        sections: List of configuration dictionaries representing individual UI sections.
        state: Optional dictionary containing runtime state values for data-binding.
        wrap_text: Boolean flag determining whether long content lines should wrap within box widths.

    Returns:
        tuple[list[dict[str, Any]], int]: A tuple containing the list of resolved section configurations
            with injected spatial metadata, and the maximum required vertical coordinate (canvas height).
    """
    # SEQUENTIAL OVERWRITING & PRE-PASS RESOLUTION (Z-INDEX LAYER SORTING)
    # Sorts inbound section definitions by their z-index rating to establish correct
    # visual stacking and rendering precedence order.
    sorted_sections = sorted(sections, key=lambda s: s.get("z_index", 0))

    rendered_bounds: dict[str, dict[str, int]] = {}
    resolved_sections: list[dict[str, Any]] = []
    max_required_y = 2  # Account for top metadata headers

    # SECTION ITERATION & SPATIAL METRIC COMPUTATION
    # Iterates through each sorted section to compute absolute or relative coordinates,
    # resolve text entries, and evaluate dynamic dimensions.
    for section in sorted_sections:
        sec = section.copy()
        section_id = sec.get("id")
        has_box = sec.get("has_box", True)

        # MANUAL COORDINATE MANAGEMENT (RELATIVE FLOW & STACKING)
        # Evaluates whether the current section should be stacked directly below a parent component
        # or positioned using explicit absolute coordinates.
        stack_below_id = sec.get("stack_below")
        if stack_below_id and stack_below_id in rendered_bounds:
            parent = rendered_bounds[stack_below_id]
            box_x = parent["x"]
            box_y = parent["y"] + parent["h"] + 1  # 1-row gap spacing
        else:
            box_x = sec.get("x", 0)
            box_y = sec.get("y", 2)

        # RESOLUTION PROTOCOLS: ENTRY & TEMPLATE EVALUATION
        # Processes section entries, applying hotkeys, auto-incremented numbering,
        # and runtime state reference binding.
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

        # CONTENT SOURCE SELECTION (RAW BLOCK VS STRUCTURED TEMPLATES)
        # Determines whether the section displays structured template rows or raw multiline text blocks.
        source_lines: Sequence[str] = []
        if is_raw_block and entries:
            raw_content = state.get(entries[0].get("state_ref"), "") if state else ""
            source_lines = raw_content.splitlines()
        else:
            source_lines = rendered_lines

        # SECTION WIDTH RESOLUTION & AUTO-SIZING
        # Calculates dynamic box width based on content length or default configuration constraints.
        box_w = sec.get("w", 40)
        if box_w == "auto":
            max_line_len = max((len(line) for line in source_lines), default=10)
            box_w = max_line_len + (4 if has_box else 0)

        # SECTION HEIGHT RESOLUTION (h="auto" SUPPORT & TEXT WRAPPING)
        # Computes dynamic height requirements, accounting for text wrapping and box borders.
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
        # Injects computed spatial coordinates into the section dictionary and updates global bounds cache.
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

    return resolved_sections, max_required_y


# ENTRY RESOLUTION & STATE POLL COMPOSITOR ENGINE
# This utility processes section entry definitions, resolving hotkeys or auto-incremented
# identifiers, polling runtime session state references, and formatting final string lines
# using template blueprints.
# [>] EXECUTING ENTRY RESOLUTION & STATE BINDING
def resolve_entries(
    entries: list[dict[str, Any]],
    state: dict[str, Any] | None,
    id_type: str,
    template: str,
) -> list[str]:
    """
    Resolves coordinate keys, polls runtime session state, and formats
    entry strings using the provided template blueprint.

    Args:
        entries: List of dictionary definitions representing individual menu or data items.
        state: Optional dictionary containing runtime state values for reference lookups.
        id_type: Strategy identifier for row indexing ('auto_int' vs custom hotkeys).
        template: String format template blueprint for rendering keys, labels, and values.

    Returns:
        list[str]: A list of formatted string lines ready for layout synthesis and text wrapping.
    """
    # RENDERED ENTRY COLLECTION INITIALIZATION
    rendered_entries: list[str] = []

    # ENTRY ITERATION & STATE BINDING
    # Iterates through each entry configuration to resolve unique keys, poll state values,
    # and format the row according to the given template.
    for i, entry in enumerate(entries):
        # KEY RESOLUTION (AUTO-INCREMENT VS HOTKEY)
        # Determines whether to assign an automatic integer index or an explicit hotkey string.
        key = str(i + 1) if id_type == "auto_int" else entry.get("hotkey", "")

        # RUNTIME STATE POLL & DEFAULT FALLBACK
        # Safely polls the active session state dictionary using the specified reference key,
        # falling back to 'N/A' if the state or reference is missing.
        val = ""
        if state and "state_ref" in entry:
            val = str(state.get(entry["state_ref"], "N/A"))

        # TEMPLATE FORMATTING & LINE APPEND
        # Applies the target format string template to combine key, label, and polled value data.
        rendered_entries.append(
            template.format(key=key, label=entry.get("label", ""), val=val)
        )

    return rendered_entries
