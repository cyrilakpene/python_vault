from .constants import border_styles  # type: ignore[import-not-found]


# 2D RASTERIZATION & ABSOLUTE TEXT PLACEMENT ENGINE
# This utility handles the low-level rendering of string content into a 2D character buffer.
# By enforcing strict boundary checking per character coordinate, it prevents out-of-bounds
# index errors during grid manipulation and layout synthesis.
def draw_text(
    x: int,
    y: int,
    text: str,
    canvas_width: int,
    canvas_height: int,
    buffer: list[list[str]],
) -> None:
    """
    Safely writes a string horizontally into the 2D buffer at a specific coordinate.

    Args:
        x: Starting horizontal coordinate (column index) for the text placement.
        y: Vertical coordinate (row index) where the text line is rendered.
        text: The string sequence to render into the buffer.
        canvas_width: Maximum allowed width constraint for boundary validation.
        canvas_height: Maximum allowed height constraint for boundary validation.
        buffer: The 2D grid character matrix being mutated in-place.
    """
    # HORIZONTAL CHARACTER ITERATION & BUFFER MUTATION
    # Iterates through each character in the target text string, computing its absolute
    # 2D coordinate offset and writing it directly to the active canvas matrix.
    for i, char in enumerate(text):
        # BOUNDARY GUARD: MATRIX SAFETY CHECK
        # Ensures both the horizontal position (accounting for text progression via index 'i')
        # and the vertical coordinate 'y' reside strictly within the permitted canvas dimensions
        # to prevent IndexError exceptions in the 2D buffer array.
        if 0 <= x + i < canvas_width and 0 <= y < canvas_height:
            # MEMORY WRITE: IN-PLACE CELL ASSIGNMENT
            # Safely injects the validated character into the target grid coordinate.
            buffer[y][x + i] = char


# 2D RASTERIZATION & ABSOLUTE BOX FRAME COMPOSITOR ENGINE
# This utility renders structured framing geometry and window boundaries into the 2D character buffer.
# By supporting custom or preset border glyph styles and conditional title injection, it constructs
# reliable visual containers while enforcing strict viewport boundary checks.
# [>] EXECUTING ABSOLUTE BOX FRAME COMPOSITOR
def draw_box(
    start_x: int,
    start_y: int,
    w: int,
    h: int,
    buffer: list[list[str]],
    border_style: str | dict[str, str],
    title: str = "",
    canvas_width: int = 80,
    canvas_height: int = 24,
) -> None:
    """
    Draws a framed structural window with an optional title and configurable borders at precise grid bounds.

    Args:
        start_x: Starting horizontal coordinate (column index) for the top-left box origin.
        start_y: Starting vertical coordinate (row index) for the top-left box origin.
        w: Total width of the box frame including borders.
        h: Total height of the box frame including borders.
        buffer: The 2D grid character matrix being mutated in-place.
        border_style: Preset style name string or custom mapping dictionary for corner/edge glyphs.
        title: Optional string label rendered inside the top border.
        canvas_width: Maximum allowed width constraint for boundary validation.
        canvas_height: Maximum allowed height constraint for boundary validation.
    """
    # STYLE RESOLUTION & CHARACTER SET MAPPING
    # Resolves the requested border style argument into a concrete character map dictionary,
    # falling back to default presets if a string name is provided.
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

    # HORIZONTAL BOUNDARY RENDERING & BUFFER MUTATION
    # Iterates across the horizontal span of the box width to paint top and bottom edge glyphs,
    # validating each coordinate against canvas dimension limits.
    for x in range(start_x, start_x + w):
        if 0 <= start_y < canvas_height and 0 <= x < canvas_width:
            buffer[start_y][x] = h_char
        if 0 <= start_y + h - 1 < canvas_height and 0 <= x < canvas_width:
            buffer[start_y + h - 1][x] = h_char

    # VERTICAL BOUNDARY RENDERING & BUFFER MUTATION
    # Iterates across the vertical span of the box height to paint left and right edge glyphs,
    # ensuring safe boundary checking prior to cell assignment.
    for y in range(start_y, start_y + h):
        if 0 <= y < canvas_height and 0 <= start_x < canvas_width:
            buffer[y][start_x] = v_char
        if 0 <= y < canvas_height and 0 <= start_x + w - 1 < canvas_width:
            buffer[y][start_x + w - 1] = v_char

    # CORNER GLYPH PLACEMENT & BOUNDARY VALIDATION
    # Positions specific intersection glyphs (top-left, top-right, bottom-left, bottom-right)
    # at the four absolute vertices of the box frame.
    if 0 <= start_y < canvas_height and 0 <= start_x < canvas_width:
        buffer[start_y][start_x] = tl
    if 0 <= start_y < canvas_height and 0 <= start_x + w - 1 < canvas_width:
        buffer[start_y][start_x + w - 1] = tr
    if 0 <= start_y + h - 1 < canvas_height and 0 <= start_x < canvas_width:
        buffer[start_y + h - 1][start_x] = bl
    if 0 <= start_y + h - 1 < canvas_height and 0 <= start_x + w - 1 < canvas_width:
        buffer[start_y + h - 1][start_x + w - 1] = br

    # OPTIONAL TITLE INJECTION & COMPOSITING
    # Conditionally injects a formatted title string into the top border segment
    # using the absolute text placement utility.
    if title:
        draw_text(
            start_x + 2, start_y, f"[{title}]", canvas_width, canvas_height, buffer
        )
