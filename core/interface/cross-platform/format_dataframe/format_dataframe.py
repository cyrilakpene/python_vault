from __future__ import annotations
from typing import TYPE_CHECKING, Any, Iterable, Literal, Mapping, Sequence, cast

from interface.report_status import report_status  # type: ignore[import-not-found]
from security.runtime_context import log_path  # type: ignore[import-not-found]

# TYPE SYSTEM INTEGRATION & CONDITIONAL ANNOTATION ALIASING
# This structural typing directive establishes a flexible data container type alias (`TabularData`)
# across the runtime and static analysis boundary. Under static analysis, it enforces strict structural
# type checking against DataFrames, iterable mappings, or positional sequences. At runtime, it resolves
# to an unconstrained wildcard to avoid unnecessary type resolution overhead and circular imports.
if TYPE_CHECKING:
    import pandas as pd  # type: ignore[import-not-found]

    # STATIC ANALYSIS TYPE ALIAS DISPATCH
    # Maps complex union type signatures representing polymorphic tabular inputs for static linters.
    TabularData = pd.DataFrame | Iterable[Mapping[str, Any]] | Iterable[Sequence[Any]]
else:
    # RUNTIME TYPE FALLBACK ALIASING
    # Simplifies structural type resolution to `Any` during standard Python execution loops.
    TabularData = Any


# HIGH-PERFORMANCE TABULAR STRINGIFICATION & DISPLAY ENGINE
# This core formatting function converts heterogeneous tabular data formats—such as pandas DataFrames,
# lists of dictionaries, or nested sequences—into aligned, terminal-ready ASCII text tables. By resolving
# dynamic column widths, structural text alignment, cell padding, and header signatures in a single
# execution pass, it establishes a unified visualization layer for CLI output streams.
def format_dataframe(
    df: TabularData,
    col_width: int | dict[str, int] | Literal["auto"] = "auto",
    align: Literal["<", ">", "^", "auto"] | dict[str, str] = "auto",
    padding: int = 2,
    strip_index: bool = False,
    headers: Sequence[str] | Literal["auto"] = "auto",
) -> str:
    """Formats tabular data (DataFrame, list of dicts, or nested sequences) into an aligned text table.

    Transforms structured tabular data into a clean, human-readable ASCII table,
    evaluating column widths, alignment rules, and cell truncation in a single
    encapsulated pass. Supports pandas DataFrames as well as standard Python structures
    like lists of dictionaries or lists of lists/tuples.

    Args:
        df: The target tabular dataset (pandas DataFrame, Iterable[dict], or Iterable[sequence]).
        col_width: Column width specifier ("auto", uniform integer, or column-mapped dict).
        align: Text alignment specifier ("<", ">", "^", "auto", or column-mapped dict).
        padding: Horizontal spacing in characters inserted between adjacent columns.
        strip_index: If True, excludes the DataFrame index (applies to pandas DataFrames).
        headers: Column header names when passing sequences without inherent keys ("auto" or list).

    Returns:
        A fully formatted, multiline text representation of the input table.
    """

    report_status(
        state="task",
        message="Initializing tabular data formatting sequence.",
        silent=True,
        log_path=log_path,
    )

    # DATA NORMALIZATION PIPELINE & STATE ACCUMULATION
    # Instantiates intermediate collection structures to capture normalized string matrices,
    # header signatures, and inferred numeric column metadata prior to alignment computation.
    cols: list[str] = []
    matrix: list[list[str]] = []
    numeric_cols: set[str] = set()

    # RUNTIME DEPENDENCY SAFEGUARD & DATAFRAME PROFILES
    # Safely checks for pandas availability without forcing global imports, capturing the module reference
    # if the target input satisfies DataFrame type signatures for specialized index/type routines.
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
            state="info]",
            message="pandas module not available in environment.",
            silent=True,
            log_path=log_path,
        )

    # DATAFRAME PARSING & MATRIX VECTORIZATION BRANCH
    # Processes native pandas DataFrame objects by evaluating index visibility, extracting string-coerced
    # header lists, identifying numeric column metadata for auto-alignment, and vectorizing full row matrices.
    if pd_module is not None:
        pd_df = cast("pd.DataFrame", df)

        # EMPTY DATASET GUARD CLAUSE
        # Halts rendering and returns an empty string payload if the provided DataFrame contains no data rows.
        if pd_df.empty:
            report_status(
                state="warn",
                message="Input DataFrame is empty. Aborting formatting.",
                silent=True,
                log_path=log_path,
            )
            return ""

        # INDEX INTEGRATION & STRUCTURAL FLATTENING
        # Evaluates the `strip_index` directive to conditionally project index series into explicit dataframe columns.
        target_df = pd_df.reset_index() if not strip_index else pd_df

        # COLUMN HEADER COERCION
        # Converts header keys across the target DataFrame into uniform string signatures.
        cols = [str(c) for c in target_df.columns]

        report_status(
            state="info",
            message=f"Resolved DataFrame columns: {cols}",
            silent=True,
            log_path=log_path,
        )

        # NUMERIC COLUMN METADATA EXTRACTION
        # Scans column data types prior to string coercion to register numeric fields for right-aligned UI display.
        for c in target_df.columns:
            if str(target_df[c].dtype).startswith(("int", "float")):
                numeric_cols.add(str(c))
        report_status(
            state="info",
            message=f"Identified numeric columns: {list(numeric_cols)}",
            silent=True,
            log_path=log_path,
        )

        # STRING MATRIX VECTORIZATION
        # Converts the normalized pandas DataFrame into a two-dimensional list of string cells for downstream rendering.
        matrix = target_df.astype(str).values.tolist()

        report_status(
            state="info",
            message=f"Vectorized DataFrame into {len(matrix)} rows.",
            silent=True,
            log_path=log_path,
        )

    # ITERABLE & DICTIONARY MATRIX PARSING BRANCH
    # Handles non-pandas tabular inputs by validating iterable capabilities, materializing dynamic generators,
    # and parsing dictionary mappings into unified matrix structures while inferring column datatypes.
    else:
        # NON-ITERABLE GUARD CLAUSE
        # Validates that input implements iteration protocol; immediately returns empty string if uniterable.
        if not hasattr(df, "__iter__"):
            report_status(
                state="fail",
                message="Input object is not iterable. Unable to format.",
                log_path=log_path,
            )
            return ""

        # GENERATOR MATERIALIZATION & EMPTY INPUT GUARD
        # Materializes single-use iterators into concrete memory lists and halts execution if dataset contains no records.
        raw_records = list(df) if not isinstance(df, list) else df
        if not raw_records:
            report_status(
                state="warn",
                message="Iterable dataset is empty. Aborting formatting.",
                silent=True,
                log_path=log_path,
            )
            return ""

        first_row = raw_records[0]

        # BRANCH A: DICTIONARY MAPPING STRUCTURAL RESOLUTION
        # Parses lists or sequences of dictionary records by discovering unique keys, building explicit string matrices,
        # and tracking candidate numeric types across heterogeneous fields.
        if isinstance(first_row, Mapping):
            report_status(
                state="info",
                message="Processing iterable of dictionary mappings.",
                silent=True,
                log_path=log_path,
            )
            dict_records = cast(list[Mapping[str, Any]], raw_records)

            # DYNAMIC COLUMN HEADER DISCOVERY
            # Scans all dictionary key-sets to preserve original key ordering and establish a comprehensive column schema.
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

            # NUMERIC STATE INFERENCE INITIALIZATION
            # Pre-populates candidate numeric column references; iteratively prunes non-numeric candidates during traversal.
            candidate_numerics = set(cols)

            # MATRIX POPULATION & COLUMN DTYPE AUDITING
            # Iterates through dictionary records, extracting cell values, coercing nulls, and discarding non-numeric type candidates.
            for dict_row in dict_records:
                dict_vals: list[str] = []
                for col in cols:
                    val = dict_row.get(col, "")
                    if val != "" and val is not None:
                        if not isinstance(val, (int, float)) or isinstance(val, bool):
                            candidate_numerics.discard(col)
                    dict_vals.append("" if val is None else str(val))
                matrix.append(dict_vals)

            # NUMERIC COLUMN ASSIGNMENT
            # Registers remaining numeric candidate keys into global numeric metadata structure.
            numeric_cols = candidate_numerics
            report_status(
                state="info",
                message=f"Inferred numeric columns: {list(numeric_cols)}",
                silent=True,
                log_path=log_path,
            )

        # BRANCH B: SEQUENCE OF POSITIONAL ELEMENTS (LISTS / TUPLES)
        # Parses positional data structures (nested lists or tuples) into standard tabular frames.
        # Determines maximum row width to accommodate uneven sequences, projects synthetic or custom headers,
        # and audits scalar values to infer numeric alignments.
        else:
            report_status(
                state="info",
                message="Processing iterable of positional sequences.",
                silent=True,
                log_path=log_path,
            )
            seq_records = cast(list[Sequence[Any]], raw_records)
            max_cols = max(len(s) for s in seq_records)

            # HEADER CONFIGURATION RESOLUTION
            # Binds explicit custom headers if provided, or generates positional default column labels ('col_0', 'col_1', etc.).
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

            # NUMERIC STATE INFERENCE INITIALIZATION
            # Pre-populates candidate numeric column references for positional sequence indices.
            candidate_numerics = set(cols)

            # MATRIX POPULATION & BOUNDARY SAFEGUARDED EXTRACTION
            # Converts sequence elements to string matrix cells, handles padding for short rows, and prunes non-numeric type candidates.
            for seq_row in seq_records:
                seq_vals: list[str] = []
                for i in range(len(cols)):
                    val = seq_row[i] if i < len(seq_row) else ""
                    if val != "" and val is not None:
                        if not isinstance(val, (int, float)) or isinstance(val, bool):
                            candidate_numerics.discard(cols[i])
                    seq_vals.append("" if val is None else str(val))
                matrix.append(seq_vals)

            # NUMERIC COLUMN METADATA REGISTRATION
            # Registers validated positional numeric column keys into the global alignment registry.
            numeric_cols = candidate_numerics
            report_status(
                state="info",
                message=f"Inferred numeric columns: {list(numeric_cols)}",
                silent=True,
                log_path=log_path,
            )

    # PADDING BUFFER & COLUMN WIDTH RESOLUTION ENGINE
    # Computes whitespace padding intervals and calculates exact character width budgets for every target column.
    # Dynamically adapts to explicit width dicts, uniform integer constraints, or automatic content-aware bounds.
    report_status(
        state="proc",
        message="Computing column widths and text alignments...",
        silent=True,
        log_path=log_path,
    )
    pad = " " * padding

    # WIDTH DYNAMICS RESOLUTION & COLUMN BOUND COMPUTATION
    # Iterates over resolved column headers to assign target character display widths based on user specifications
    # or peak content length across all matrix rows.
    widths: dict[str, int] = {}
    for col_idx, col in enumerate(cols):
        # MAPPED DICTIONARY SPECIFICATION BRANCH
        # Applies explicit column-mapped width budgets, falling back to header length for unmapped fields.
        if isinstance(col_width, dict):
            widths[col] = col_width.get(col, len(col))
        # UNIFORM INTEGER SPECIFICATION BRANCH
        # Applies a fixed, uniform character width budget across all table columns.
        elif isinstance(col_width, int):
            widths[col] = col_width
        # AUTOMATIC CONTENT-AWARE FITTING BRANCH
        # Scans matrix cells and header string lengths to establish minimal bounding widths without truncation.
        else:  # "auto" fitting
            max_val_len = max((len(row[col_idx]) for row in matrix), default=0)
            widths[col] = max(len(col), max_val_len)

    # ALIGNMENT POLICY RESOLUTION & DIRECTIONAL DISPATCH
    # Determines exact text justification routines ('<', '>', '^') for each column.
    # Evaluates explicit directional rules, uniform alignment parameters, or fallback auto-detection logic
    # that right-aligns numeric data vectors while left-aligning general text strings.
    alignments: dict[str, str] = {}
    for col in cols:
        # MAPPED DICTIONARY ALIGNMENT SPECIFICATION
        # Retrieves custom justification flags per column key, defaulting to left-alignment for missing fields.
        if isinstance(align, dict):
            alignments[col] = align.get(col, "<")
        # UNIFORM DIRECTIONAL ALIGNMENT SPECIFICATION
        # Enforces a global justification directive across all columns (left, right, or centered).
        elif align in ("<", ">", "^"):
            alignments[col] = align
        # AUTOMATIC DIRECTIONAL INFERENCE BRANCH
        # Directs numeric columns to right-alignment ('>') and general text columns to left-alignment ('<').
        else:  # "auto" mode
            alignments[col] = ">" if col in numeric_cols else "<"

    # CELL RENDERING HELPER SUBROUTINE
    # Standardizes cell-level string truncation and directional formatting based on resolved column budgets.
    def format_cell(val: str, col: str) -> str:
        w = widths[col]
        # BOUNDARY TRUNCATION
        # Hard-clips cell string contents with an ellipsis indicator if they exceed the calculated maximum column width.
        if len(val) > w:
            val = val[: w - 1] + "…" if w > 1 else val[:w]
        # FORMAT SPECIFIER APPLICATION
        # Applies directional alignment and whitespace padding according to the target column rule.
        return f"{val:{alignments[col]}{w}}"

    # HEADER RENDERING & HORIZONTAL LAYOUT ASSEMBLY
    # Formats and joins all individual header cells into a single padded header line.
    header_str = pad.join(format_cell(col, col) for col in cols)

    # BODY ROW ASSEMBLY & MATRIX FORMATTING
    # Iterates over each row in the string matrix, formatting individual cells and joining them with whitespace padding.
    rows: list[str] = [
        pad.join(format_cell(val, col) for col, val in zip(cols, row_vals))
        for row_vals in matrix
    ]
    report_status(
        state="done",
        message=f"Successfully formatted table ({len(cols)} columns, {len(rows)} rows).",
        silent=True,
        log_path=log_path,
    )

    # FINAL COMPOSITION & STRING DISPATCH
    # Combines the formatted header and body row strings into a unified, multiline output payload.
    return f"{header_str}\n" + "\n".join(rows)
