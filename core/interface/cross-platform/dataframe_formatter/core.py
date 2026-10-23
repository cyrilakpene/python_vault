from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Literal, Mapping, Sequence, TypeAlias


from .alignment import compute_widths_and_alignments  # type: ignore[import-not-found]
from .parser import parse_tabular_data  # type: ignore[import-not-found]
from .renderer import render_table  # type: ignore[import-not-found]
from .constants import report_status  # type: ignore[import-not-found]
from .constants import log_path  # type: ignore[import-not-found]

if TYPE_CHECKING:
    import pandas as pd  # type: ignore[import-not-found, import-untyped]

    TabularData: TypeAlias = (
        pd.DataFrame | Iterable[Mapping[str, Any]] | Iterable[Sequence[Any]]
    )
else:
    TabularData: TypeAlias = Any


# TABULAR DATA FORMATTING & ALIGNMENT ENGINE
# This utility transforms complex tabular datasets (DataFrames, list of dicts, or nested sequences)
# into clean, aligned text tables by coordinating data parsing, width/alignment computation, and rendering.
# [>] EXECUTING TABULAR DATA FORMATTING
def format_dataframe(
    df: TabularData,
    col_width: int | dict[str, int] | Literal["auto"] = "auto",
    align: Literal["<", ">", "^", "auto"] | dict[str, str] = "auto",
    padding: int = 2,
    strip_index: bool = False,
    headers: Sequence[str] | Literal["auto"] = "auto",
) -> str:
    """
    Formats tabular data (DataFrame, list of dicts, or nested sequences) into an aligned text table.

    Args:
        df: The raw tabular data input (DataFrame, dict sequence, or 2D matrix).
        col_width: Column width configuration (uniform integer, per-column dictionary, or 'auto' fitting).
        align: Alignment configuration (explicit format token, per-column dictionary, or 'auto' mode).
        padding: Integer specifying the number of spaces between adjacent columns.
        strip_index: Boolean flag indicating whether to strip the index column from DataFrames.
        headers: Sequence of custom header strings or 'auto' for automatic header inference.

    Returns:
        str: A formatted ASCII text string representing the aligned tabular data.
    """
    report_status(
        state="task",
        message="Initializing tabular data formatting sequence.",
        silent=True,
        log_path=log_path,
    )

    # DATA NORMALIZATION & PARSING
    # Normalizes input tabular structures into uniform columns, data matrix, and numeric column identifiers.
    cols, matrix, numeric_cols = parse_tabular_data(
        df=df,
        strip_index=strip_index,
        headers=headers,
    )

    if not cols or not matrix:
        return ""

    # WIDTH & ALIGNMENT RESOLUTION
    # Computes character widths and determines text alignments for each column.
    report_status(
        state="proc",
        message="Computing column widths and text alignments...",
        silent=True,
        log_path=log_path,
    )
    widths, alignments = compute_widths_and_alignments(
        cols=cols,
        matrix=matrix,
        numeric_cols=numeric_cols,
        col_width=col_width,
        align=align,
    )

    # TABLE RENDERING & COMPOSITION
    # Assembles headers, matrix cells, widths, and padding into a unified ASCII table string.
    table_str = render_table(
        cols=cols,
        matrix=matrix,
        widths=widths,
        alignments=alignments,
        padding=padding,
    )

    report_status(
        state="done",
        message=f"Successfully formatted table ({len(cols)} columns, {len(matrix)} rows).",
        silent=True,
        log_path=log_path,
    )

    return table_str
