import contextlib
import io
import re
import sys
import time
from typing import Callable


from .models import OverlayConfig  # type: ignore[import-not-found]


# FOOTER PROMPT FORMATTING & ALIGNMENT ENGINE
# This utility formats and aligns footer prompts within overlay spatial boundaries
# based on configuration settings for text alignment and horizontal padding.
# [>] EXECUTING FOOTER PROMPT FORMATTING
def format_footer_prompt(
    footer_prompt: str, overlay_w: int, config: OverlayConfig
) -> str:
    """
    Formats and aligns the footer prompt within the overlay spatial width.

    Args:
        footer_prompt: The prompt string to format and align.
        overlay_w: The total horizontal character width of the overlay container.
        config: Configuration object containing padding and prompt alignment rules.

    Returns:
        str: The formatted and padded footer prompt string aligned according to configuration.
    """
    # LEFT ALIGNMENT FORMATTING
    # Pads the left side with horizontal spacing and left-justifies the prompt string
    # within the available overlay width.
    if config.align_prompt == "left":
        return (" " * config.padding_x) + footer_prompt.ljust(
            overlay_w - config.padding_x
        )
    # RIGHT ALIGNMENT FORMATTING
    # Right-justifies the prompt string within the available width and appends
    # the required right padding spacing.
    elif config.align_prompt == "right":
        return footer_prompt.rjust(overlay_w - config.padding_x) + (
            " " * config.padding_x
        )

    # CENTER ALIGNMENT FORMATTING (DEFAULT FALLBACK)
    # Centers the prompt string across the total overlay width when no side alignment is specified.
    return footer_prompt.center(overlay_w)


# FRAME RENDERING & ANSI BROADCAST ENGINE
# This utility serializes the 2D grid matrix, injects aligned footer prompts into the buffer,
# and broadcasts the rendered frame to stdout using ANSI cursor control sequences for smooth UI updates.
# [>] EXECUTING FRAME RENDER & BROADCAST
def render_frame(
    grid: list[list[str]],
    start_x: int,
    start_y: int,
    overlay_h: int,
    overlay_w: int,
    canvas_h: int,
    canvas_w: int,
    footer_prompt: str,
    config: OverlayConfig,
    is_update: bool = False,
) -> None:
    """
    Serializes the 2D grid matrix, injects the aligned footer prompt,
    and broadcasts the frame to stdout using ANSI control sequences.

    Args:
        grid: 2D character matrix buffer representing the canvas layout.
        start_x: Horizontal starting coordinate offset for the overlay container.
        start_y: Vertical starting coordinate offset for the overlay container.
        overlay_h: Total vertical height of the overlay window.
        overlay_w: Total horizontal width of the overlay window.
        canvas_h: Total vertical height of الحركة full terminal canvas.
        canvas_w: Total horizontal width of the full terminal canvas.
        footer_prompt: The prompt text string to display in the overlay footer.
        config: Configuration object containing overlay padding and alignment settings.
        is_update: Boolean flag indicating whether to move the cursor up for frame refreshing.
    """
    # PROMPT POSITIONING & FORMATTING
    # Computes the vertical prompt row index and formats the footer prompt string
    # according to overlay width and alignment configuration rules.
    prompt_y = start_y + overlay_h - config.padding_y
    formatted_prompt = format_footer_prompt(footer_prompt, overlay_w, config)

    # BUFFER PROMPT INJECTION
    # Iterates through the formatted prompt characters and injects them directly
    # into the grid buffer at the calculated coordinates, enforcing strict canvas boundary checks.
    for i, char in enumerate(formatted_prompt):
        if start_x + i < canvas_w and prompt_y < canvas_h:
            grid[prompt_y][start_x + i] = char

    # FRAME PAYLOAD SERIALIZATION
    # Joins the 2D grid matrix rows into a single multi-line string representation of the frame.
    frame = "\n".join("".join(row) for row in grid)

    # ANSI CURSOR POSITIONING FOR FRAME UPDATES
    # Moves the terminal cursor up by the total canvas height using ANSI escape sequences
    # if this represents an in-place frame refresh rather than an initial render.
    if is_update:
        sys.stdout.write(f"\033[{canvas_h}A")

    # STDOUT BROADCAST & BUFFER FLUSH
    # Writes the serialized frame payload to standard output and immediately flushes the buffer
    # to ensure flicker-free real-time terminal UI animation.
    sys.stdout.write(frame + "\n")
    sys.stdout.flush()


# STDOUT INTERCEPTION & LINE EXTRACTION ENGINE
# This utility handles stdout stream interception from executable callbacks and processes lines
# using start/stop range boundaries or regex pattern filtering for transient overlays.
# [>] EXECUTING STDOUT CAPTURE & LINE EXTRACTION
def capture_and_extract_lines(
    overlay_lines: list[str] | None,
    callback: Callable[[], None] | None,
    extract_pattern: str | re.Pattern[str] | None,
    extract_start: str | re.Pattern[str] | None,
    extract_stop: str | re.Pattern[str] | None,
) -> list[str]:
    """
    Handles stdout interception from callbacks and line extraction logic.

    Args:
        overlay_lines: Optional initial list of raw text lines to process.
        callback: Optional callable whose standard output is intercepted and captured.
        extract_pattern: Optional regex pattern or string to filter specific matching lines.
        extract_start: Optional boundary marker indicating the start of text range extraction.
        extract_stop: Optional boundary marker indicating the end of text range extraction.

    Returns:
        list[str]: A processed list of extracted and filtered text lines ready for overlay rendering.
    """
    # RAW LINES INITIALIZATION
    # Initializes the raw lines container using provided overlay lines or an empty list.
    raw_lines: list[str] = [] if overlay_lines is None else list(overlay_lines)

    # STDOUT STREAM INTERCEPTION & CAPTURE
    # Redirects standard output into an in-memory stream while executing the provided callback,
    # then appends all captured output lines to the raw lines buffer.
    if callback is not None and callable(callback):
        captured_stream = io.StringIO()
        with contextlib.redirect_stdout(captured_stream):
            callback()
        raw_lines.extend(captured_stream.getvalue().splitlines())

    # RANGE-BASED BOUNDARY EXTRACTION
    # Filters captured lines between defined start and stop regex patterns if both bounds are provided.
    if extract_start is not None and extract_stop is not None:
        start_pat = (
            re.compile(extract_start)
            if isinstance(extract_start, str)
            else extract_start
        )
        stop_pat = (
            re.compile(extract_stop) if isinstance(extract_stop, str) else extract_stop
        )

        processed: list[str] = []
        capturing = False
        for line in raw_lines:
            if not capturing and start_pat.search(line):
                capturing = True
            if capturing:
                processed.append(line)
            if capturing and stop_pat.search(line) and not start_pat.search(line):
                break
        return processed

    # REGEX PATTERN FILTERING
    # Filters the raw lines buffer to retain only lines matching the specified extraction pattern.
    if extract_pattern is not None:
        pat = (
            re.compile(extract_pattern)
            if isinstance(extract_pattern, str)
            else extract_pattern
        )
        return [line for line in raw_lines if pat.search(line)]

    # DEFAULT LINE MANIFEST RETURN
    # Returns the unfiltered raw lines buffer when no extraction or filtering rules are applied.
    return raw_lines


# OVERLAY LIFECYCLE & TIMER MANAGEMENT ENGINE
# This utility manages transient overlay display holds, countdown timers, interactive prompts,
# and targeted spatial wiping using ANSI control sequences for clean terminal UI dismissals.
# [>] EXECUTING OVERLAY LIFECYCLE MANAGEMENT
def handle_overlay_lifecycle(
    grid: list[list[str]],
    start_x: int,
    start_y: int,
    overlay_h: int,
    overlay_w: int,
    canvas_h: int,
    canvas_w: int,
    default_prompt: str,
    cfg: OverlayConfig,
) -> None:
    """
    Manages the interactive display hold, countdown timer, and targeted spatial wiping.

    Args:
        grid: 2D character matrix buffer representing the canvas layout.
        start_x: Horizontal starting coordinate offset for the overlay container.
        start_y: Vertical starting coordinate offset for the overlay container.
        overlay_h: Total vertical height of the overlay window.
        overlay_w: Total horizontal width of the overlay window.
        canvas_h: Total vertical height of the terminal canvas.
        canvas_w: Total horizontal width of the terminal canvas.
        default_prompt: Default footer prompt text string.
        cfg: OverlayConfig instance containing timer, auto-clear, and padding options.
    """
    # INITIAL FRAME RENDER CALL
    # Broadcasts the initial rendered frame buffer and default footer prompt to standard output.
    render_frame(
        grid=grid,
        start_x=start_x,
        start_y=start_y,
        overlay_h=overlay_h,
        overlay_w=overlay_w,
        canvas_h=canvas_h,
        canvas_w=canvas_w,
        footer_prompt=default_prompt,
        config=cfg,
        is_update=False,
    )

    # INTERACTIVE HOLD & TIMER COUNTDOWN
    # Evaluates whether a countdown timer is configured, updating the frame prompt every second
    # or pausing execution via standard input until the operator acknowledges the display.
    if cfg.timer is not None and cfg.timer > 0:
        for remaining in range(cfg.timer, 0, -1):
            render_frame(
                grid=grid,
                start_x=start_x,
                start_y=start_y,
                overlay_h=overlay_h,
                overlay_w=overlay_w,
                canvas_h=canvas_h,
                canvas_w=canvas_w,
                footer_prompt=f"Auto-clearing in {remaining}s... (Press ENTER)",
                config=cfg,
                is_update=True,
            )
            time.sleep(1.0)
    else:
        input()

    # TARGETED SPATIAL CLEARING & CANVAS COLLAPSE
    # Executes ANSI cursor movement and line deletion escape sequences to cleanly wipe
    # the transient overlay container from the terminal screen if auto-clear is enabled.
    if cfg.auto_clear:
        sys.stdout.write(f"\033[{canvas_h + 1}A")
        sys.stdout.write(f"\033[{canvas_h}M")
        sys.stdout.flush()
