from typing import Any

from .core import heuristic_grid_renderer  # type: ignore[import-not-found]


# LIVE TELEMETRY TRANSMISSION & ANSI BUFFER WRAPPER ENGINE
# This utility manages real-time, in-place terminal updates by encapsulating the rendered
# grid output with ANSI control sequences. By handling line purging, ghost artifact eradication,
# and cursor homing, it guarantees smooth live-streamed terminal visualization.
# [>] EXECUTING LIVE TELEMETRY TRANSMISSION WRAPPER
def render_live_frame(
    schema: dict[str, Any],
    state: dict[str, Any] | None = None,
    width: int = 80,
    height: int | str = "auto",
    clear_below: int = 0,
) -> str:
    """
    The live telemetry transmission wrapper for the heuristic grid engine.

    This function wraps the absolute grid output with ANSI control sequences
    designed specifically for real-time, in-place terminal updates.

    Args:
        schema: Configuration dictionary defining the UI sections and layout elements.
        state: Optional dictionary containing runtime state values for telemetry binding.
        width: Total width constraint for the rendered character grid canvas.
        height: Total height constraint or 'auto' dynamic sizing mode.
        clear_below: Number of additional trailing lines to clear below the active canvas.

    Returns:
        str: A consolidated string containing ANSI escape sequences and rendered frame lines.
    """
    # FRAME GENERATION & CORE RENDERING INVOCATION
    # Invokes the underlying heuristic grid renderer to build the raw character matrix string
    # based on the inbound schema and state configurations.
    raw_output = heuristic_grid_renderer(schema, state, width=width, height=height)

    # ANSI LINE PURGING: GHOST ARTIFACT ERADICATION
    # Appends the ANSI 'erase in line' escape sequence (\033[K) to every rendered line
    # to completely eliminate trailing visual artifacts from previous longer frames.
    cleaned_lines = [line + "\033[K" for line in raw_output.splitlines()]

    # BUFFER PADDING & SUB-CANVAS CLEARING
    # Appends empty whitespace lines padded with purge sequences if extra vertical
    # canvas clearance was requested.
    if clear_below > 0:
        canvas_w = width
        for _ in range(clear_below):
            cleaned_lines.append(" " * canvas_w + "\033[K")

    # BUFFER CONSOLIDATION: CURSOR HOMING & BROADCAST
    # Prepends the ANSI cursor home sequence (\033[H) to reposition the terminal cursor
    # to the top-left corner before joining and broadcasting the updated frame buffer.
    return "\033[H" + "\n".join(cleaned_lines)
