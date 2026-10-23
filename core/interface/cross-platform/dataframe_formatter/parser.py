from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Mapping, Sequence, TypeAlias, cast

from .constants import report_status  # type: ignore[import-not-found]
from .constants import log_path  # type: ignore[import-not-found]

if TYPE_CHECKING:
    import pandas as pd  # type: ignore[import-not-found, import-untyped]

    TabularData: TypeAlias = (
        pd.DataFrame | Iterable[Mapping[str, Any]] | Iterable[Sequence[Any]]
    )
else:
    TabularData: TypeAlias = Any


# TABULAR DATA PARSING & VECTORIZATION ENGINE
# This utility detects input data types, extracts headers, vectorizes rows into a string matrix,
# and identifies numeric columns across various data structures (Pandas DataFrames, dictionaries, and sequences).
# [>] EXECUTING TABULAR DATA PARSING & VECTORIZATION
def parse_tabular_data(
    df: TabularData,
    strip_index: bool = False,
    headers: Sequence[str] | str = "auto",
) -> tuple[list[str], list[list[str]], set[str]]:
    """
    Detects input types, extracts headers, vectorizes rows into a matrix, and identifies numeric columns.

    Args:
        df: Input tabular data (Pandas DataFrame, iterable of mappings, or iterable of sequences).
        strip_index: Whether to exclude the DataFrame index from the parsed columns/matrix.
        headers: Column headers configuration ('auto' or custom sequence of strings).

    Returns:
        tuple[list[str], list[list[str]], set[str]]: Extracted column headers, 2D string matrix of rows,
            and a set of column names identified as numeric.
    """
    cols: list[str] = []
    matrix: list[list[str]] = []
    numeric_cols: set[str] = set()

    # RUNTIME DEPENDENCY SAFEGUARD & DATAFRAME PROFILES
    # Attempts to import pandas at runtime to safely handle Pandas DataFrame inputs if available in the environment.
    pd_module = None
    try:
        import pandas as pd

        if isinstance(df, pd.DataFrame):
            pd_module = pd
            report_status(
                state="info",
                message="Detected pandas DataFrame input.",
                silent=True,
                log_path=log_path,
            )
    except ImportError:
        report_status(
            state="info",
            message="pandas module not available in environment.",
            silent=True,
            log_path=log_path,
        )

    # DATAFRAME PARSING & MATRIX VECTORIZATION BRANCH
    # Processes Pandas DataFrame inputs, handling empty checks, index inclusion/stripping,
    # header resolution, numeric dtype identification, and string vectorization.
    if pd_module is not None:
        pd_df = cast("pd.DataFrame", df)

        # DATAFRAME EMPTY VALIDATION CHECK
        if pd_df.empty:
            report_status(
                state="warn",
                message="Input DataFrame is empty. Aborting formatting.",
                silent=True,
                log_path=log_path,
            )
            return cols, matrix, numeric_cols

        # DATAFRAME INDEX & COLUMN EXTRACTION
        target_df = pd_df.reset_index() if not strip_index else pd_df
        cols = [str(c) for c in target_df.columns]

        report_status(
            state="info",
            message=f"Resolved DataFrame columns: {cols}",
            silent=True,
            log_path=log_path,
        )

        # NUMERIC DATATYPE IDENTIFICATION LOOP
        for c in target_df.columns:
            if str(target_df[c].dtype).startswith(("int", "float")):
                numeric_cols.add(str(c))
        report_status(
            state="info",
            message=f"Identified numeric columns: {list(numeric_cols)}",
            silent=True,
            log_path=log_path,
        )

        # DATAFRAME TO MATRIX VECTORIZATION
        matrix = target_df.astype(str).values.tolist()

        report_status(
            state="info",
            message=f"Vectorized DataFrame into {len(matrix)} rows.",
            silent=True,
            log_path=log_path,
        )

    # ITERABLE & DICTIONARY MATRIX PARSING BRANCH
    # Fallback branch for non-DataFrame iterables, supporting collections of dictionary mappings
    # or positional sequences (lists/tuples).
    else:
        # ITERABILITY VALIDATION CHECK
        if not hasattr(df, "__iter__"):
            report_status(
                state="fail",
                message="Input object is not iterable. Unable to format.",
                log_path=log_path,
            )
            return cols, matrix, numeric_cols

        raw_records: list[Any] = (
            list(df) if not isinstance(df, list) else cast(list[Any], df)
        )

        # RECORD COLLECTION EMPTY VALIDATION CHECK
        if not raw_records:
            report_status(
                state="warn",
                message="Iterable dataset is empty. Aborting formatting.",
                silent=True,
                log_path=log_path,
            )
            return cols, matrix, numeric_cols

        first_row = raw_records[0]

        # BRANCH A: DICTIONARY MAPPING STRUCTURAL RESOLUTION
        # Processes iterables of dictionaries, aggregating unique keys, extracting values,
        # and inferring numeric columns based on value types.
        if isinstance(first_row, Mapping):
            report_status(
                state="info",
                message="Processing iterable of dictionary mappings.",
                silent=True,
                log_path=log_path,
            )
            dict_records = cast(list[Mapping[str, Any]], raw_records)

            seen_keys: dict[str, None] = {}
            for dict_row in dict_records:
                for key in dict_row.keys():
                    seen_keys[str(key)] = None
            cols = list(seen_keys.keys())
            report_status(
                state="info",
                message=f"Discovered keys: {cols}",
                silent=True,
                log_path=log_path,
            )

            candidate_numerics = set(cols)

            for dict_row in dict_records:
                dict_vals: list[str] = []
                for col in cols:
                    val = dict_row.get(col, "")
                    if val != "" and val is not None:
                        if not isinstance(val, (int, float)) or isinstance(val, bool):
                            candidate_numerics.discard(col)
                    dict_vals.append("" if val is None else str(val))
                matrix.append(dict_vals)

            numeric_cols = candidate_numerics
            report_status(
                state="info",
                message=f"Inferred numeric columns: {list(numeric_cols)}",
                silent=True,
                log_path=log_path,
            )

        # BRANCH B: SEQUENCE OF POSITIONAL ELEMENTS (LISTS / TUPLES)
        # Processes iterables of sequences, assigning automatic or custom headers,
        # padding missing values, and inferring numeric columns.
        else:
            report_status(
                state="info",
                message="Processing iterable of positional sequences.",
                silent=True,
                log_path=log_path,
            )
            seq_records = cast(list[Sequence[Any]], raw_records)
            max_cols = max(len(s) for s in seq_records)

            if headers != "auto":
                cols = [str(h) for h in headers]
            else:
                cols = [f"col_{i}" for i in range(max_cols)]
            report_status(
                state="info",
                message=f"Assigned sequence headers: {cols}",
                silent=True,
                log_path=log_path,
            )

            candidate_numerics = set(cols)

            for seq_row in seq_records:
                seq_vals: list[str] = []
                for i in range(len(cols)):
                    val = seq_row[i] if i < len(seq_row) else ""
                    if val != "" and val is not None:
                        if not isinstance(val, (int, float)) or isinstance(val, bool):
                            candidate_numerics.discard(cols[i])
                    seq_vals.append("" if val is None else str(val))
                matrix.append(seq_vals)

            numeric_cols = candidate_numerics
            report_status(
                state="info",
                message=f"Inferred numeric columns: {list(numeric_cols)}",
                silent=True,
                log_path=log_path,
            )

    # PARSING RESULTS MANIFEST RETURN
    # Returns the resolved column headers, string matrix, and identified numeric columns.
    return cols, matrix, numeric_cols
