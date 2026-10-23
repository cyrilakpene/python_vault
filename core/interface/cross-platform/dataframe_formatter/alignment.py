from __future__ import annotations

from typing import Literal


# COLUMN WIDTH & ALIGNMENT RESOLUTION ENGINE
# This utility computes dynamic character display widths and resolves alignment specifiers per column.
# By supporting custom dictionary mappings, fixed integer dimensions, or automatic content-based fitting
# alongside smart numeric right-alignment, it ensures clean tabular layouts for terminal UI components.
# [>] EXECUTING WIDTH & ALIGNMENT COMPUTATION
def compute_widths_and_alignments(
    cols: list[str],
    matrix: list[list[str]],
    numeric_cols: set[str],
    col_width: int | dict[str, int] | Literal["auto"] = "auto",
    align: Literal["<", ">", "^", "auto"] | dict[str, str] = "auto",
) -> tuple[dict[str, int], dict[str, str]]:
    """
    Computes dynamic character display widths and resolves alignment specifiers per column.

    Args:
        cols: List of column header name strings.
        matrix: 2D list of row string values populating the table structure.
        numeric_cols: Set of column names identified as numeric types for smart alignment.
        col_width: Column width configuration (uniform integer, per-column dictionary, or 'auto' fitting).
        align: Alignment configuration (explicit format token, per-column dictionary, or 'auto' mode).

    Returns:
        tuple[dict[str, int], dict[str, str]]: A tuple containing the computed character widths dictionary
            and the resolved text alignments dictionary.
    """
    # COLUMN WIDTH COMPUTATION & FITTING LOOP
    # Iterates through each column definition to determine its display character width,
    # respecting explicit dictionaries, uniform integer widths, or automatic content-based fitting.
    widths: dict[str, int] = {}
    for col_idx, col in enumerate(cols):
        if isinstance(col_width, dict):
            widths[col] = col_width.get(col, len(col))
        elif isinstance(col_width, int):
            widths[col] = col_width
        else:  # "auto" fitting
            max_val_len = max((len(row[col_idx]) for row in matrix), default=0)
            widths[col] = max(len(col), max_val_len)

    # COLUMN ALIGNMENT RESOLUTION LOOP
    # Resolves alignment specifiers per column, evaluating custom dictionary overrides,
    # explicit formatting characters, or automatic rules (right-aligning numeric columns).
    alignments: dict[str, str] = {}
    for col in cols:
        if isinstance(align, dict):
            alignments[col] = align.get(col, "<")
        elif align in ("<", ">", "^"):
            alignments[col] = align
        else:  # "auto" mode
            alignments[col] = ">" if col in numeric_cols else "<"

    # WIDTH & ALIGNMENT MANIFEST RETURN
    # Returns the completed dictionaries defining column character widths and text alignments.
    return widths, alignments
