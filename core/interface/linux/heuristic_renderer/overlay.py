import re
from typing import Callable


from .models import OverlayConfig  # type: ignore[import-not-found]
from .frame import capture_and_extract_lines, handle_overlay_lifecycle  # type: ignore[import-not-found]
from .compositor import draw_box, draw_text  # Integrated from compositor_2


# TRANSIENT 2D OVERLAY COMPOSITOR LAYER
# TRANSIENT OVERLAY DISPLAY & FRAME MANAGEMENT ENGINE
# This utility provides a standalone 2D frame manager that displays transient text inside
# bordered or imaginary regions, coordinating stdout interception, pattern/range extraction,
# spatial boundary computations, canvas buffer painting, and lifecycle management.
# [>] EXECUTING TRANSIENT OVERLAY DISPLAY
def display_transient_overlay(
    overlay_lines: list[str] | None = None,
    callback: Callable[[], None] | None = None,
    extract_pattern: str | re.Pattern[str] | None = None,
    extract_start: str | re.Pattern[str] | None = None,
    extract_stop: str | re.Pattern[str] | None = None,
    config: OverlayConfig | None = None,
    border_style: str | dict[str, str] | None = None,
) -> None:
    """
    A standalone 2D frame manager that displays transient text inside an imaginary
    or bordered region with dynamic stdout interception, pattern/range extraction,
    and targeted spatial wiping.

    Args:
        overlay_lines: Optional pre-existing list of string lines to render directly.
        callback: Optional executable function whose stdout output is intercepted and captured.
        extract_pattern: Optional regex pattern or string to filter and extract specific captured lines.
        extract_start: Optional boundary marker string or regex indicating the start of text extraction.
        extract_stop: Optional boundary marker string or regex indicating the end of text extraction.
        config: Optional OverlayConfig instance defining padding, dimensions, and prompt behavior.
        border_style: Optional string name or dictionary specifying border drawing styles.
    """
    # OVERLAY CONFIGURATION INITIALIZATION
    # Fallbacks to default overlay configuration parameters if none are explicitly provided.
    cfg = config or OverlayConfig()

    # CONTENT EXTRACTION & CAPTURE
    # Intercepts stdout execution streams or filters provided lines based on pattern and boundary rules.
    lines = capture_and_extract_lines(
        overlay_lines, callback, extract_pattern, extract_start, extract_stop
    )

    default_prompt_line = cfg.prompt

    # SPATIAL BOUNDARY & DIMENSION COMPUTATION
    # Calculates maximum line lengths, border offsets, and overall overlay window width and height.
    max_line_len = max([len(l) for l in lines] + [len(default_prompt_line)], default=0)
    has_border = border_style is not None

    border_offset_x = 4 if has_border else (cfg.padding_x * 2)
    border_offset_h = 3 if has_border else (cfg.padding_y * 2)

    overlay_w = max(max_line_len + border_offset_x, len(default_prompt_line) + 2)
    overlay_h = len(lines) + border_offset_h + 1

    canvas_w = int(cfg.width)
    canvas_h = overlay_h
    start_x = max(0, (canvas_w - overlay_w) // 2)
    start_y = 0

    # CANVAS BUFFER INITIALIZATION & BORDER RENDERING
    # Allocates a 2D whitespace character grid matrix and draws decorative container borders
    # if a border style is configured.
    grid = [[" " for _ in range(canvas_w)] for _ in range(canvas_h)]

    if border_style is not None:
        draw_box(
            start_x=start_x,
            start_y=start_y,
            w=overlay_w,
            h=overlay_h - 1,
            buffer=grid,
            border_style=border_style,
            canvas_width=canvas_w,
            canvas_height=canvas_h,
        )

    content_padding_x = 2 if has_border else cfg.padding_x
    content_padding_y = 1 if has_border else cfg.padding_y

    # CONTENT TEXT PAINTING
    # Iterates through extracted text lines and paints them into the grid buffer
    # at coordinates offset by computed padding and starting positions.
    for line_idx, line in enumerate(lines):
        draw_text(
            x=start_x + content_padding_x,
            y=start_y + content_padding_y + line_idx,
            text=line,
            canvas_width=canvas_w,
            canvas_height=canvas_h,
            buffer=grid,
        )

    # LIFECYCLE DELEGATION & FRAME MANAGEMENT
    # Delegates rendering, timer management, interactive prompts, and cleanup wiping
    # to the overlay lifecycle controller.
    handle_overlay_lifecycle(
        grid=grid,
        start_x=start_x,
        start_y=start_y,
        overlay_h=overlay_h,
        overlay_w=overlay_w,
        canvas_h=canvas_h,
        canvas_w=canvas_w,
        default_prompt=default_prompt_line,
        cfg=cfg,
    )
