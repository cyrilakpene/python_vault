from __future__ import annotations


# CELL FORMATTING & TRUNCATION ENGINE
# This utility standardizes cell-level string formatting by handling character truncation with ellipsis
# overflow indicators and applying precise alignment and width specifiers for terminal tables.
# [>] EXECUTING CELL FORMATTING & TRUNCATION
def format_cell(
    val: str,
    col: str,
    width: int,
    alignment: str,
) -> str:
    """
    Standardizes cell-level string truncation and applies format specifiers.

    Args:
        val: The raw string value to format for the table cell.
        col: The column header name associated with the cell (for contextual tracking).
        width: The maximum character width allowed for the cell display.
        alignment: The format specifier alignment character (e.g., '<', '>', '^').

    Returns:
        str: The formatted, truncated, and padded cell string ready for tabular layout.
    """
    # STRING TRUNCATION & ELLIPSIS OVERFLOW HANDLING
    # Checks if the value exceeds the maximum allowable column width, truncating it
    # and appending an ellipsis character if space permits.
    if len(val) > width:
        val = val[: width - 1] + "…" if width > 1 else val[:width]

    # FORMAT SPECIFIER APPLICATION
    # Applies the resolved column width and text alignment formatting using Python's format specification mini-language.
    return f"{val:{alignment}{width}}"


# TABULAR RENDERING & ASCII GRID COMPOSITION ENGINE
# This utility formats table headers and data rows by applying computed widths and alignments,
# joining them with configurable padding into a unified, structured tabular ASCII string.
# [>] EXECUTING TABULAR RENDER COMPOSITION
def render_table(
    cols: list[str],
    matrix: list[list[str]],
    widths: dict[str, int],
    alignments: dict[str, str],
    padding: int = 2,
) -> str:
    """
    Formats cells, headers, and rows, joining them into a unified tabular ASCII string.

    Args:
        cols: List of column header name strings.
        matrix: 2D list of row string values populating the table structure.
        widths: Dictionary mapping each column name to its computed character width.
        alignments: Dictionary mapping each column name to its text alignment specifier.
        padding: Integer specifying the number of spaces between adjacent columns.

    Returns:
        str: A consolidated multi-line string representing the rendered ASCII table.
    """
    # PADDING SPACING INITIALIZATION
    # Generates the horizontal whitespace separator string based on the configured padding width.
    pad = " " * padding

    # HEADER CELL FORMATTING & ALIGNMENT
    # Formats each column header name using its resolved width and alignment specifier,
    # joining them with the padding separator.
    header_str = pad.join(
        format_cell(col, col, widths[col], alignments[col]) for col in cols
    )

    # ROW MATRIX FORMATTING & PADDING APPLICATION
    # Iterates through each data row in the matrix, zipping values with column configurations
    # to format and align every cell before joining them into tabular rows.
    rows: list[str] = [
        pad.join(
            format_cell(val, col, widths[col], alignments[col])
            for col, val in zip(cols, row_vals)
        )
        for row_vals in matrix
    ]

    # TABULAR BUFFER CONSOLIDATION
    # Combines the formatted header string and all rendered rows into a single newline-delimited output.
    return f"{header_str}\n" + "\n".join(rows)
