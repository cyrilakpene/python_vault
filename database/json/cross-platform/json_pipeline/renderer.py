import json
from typing import Any, cast

from .sanitizer import trace  # type: ignore[import-not-found]
from .constants import report_status, log_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: FLAT PATH RENDERER & SERIALIZER
# This utility unrolls target data structures into flat (path, value) tuples
# and serializes them into aligned text strings for CLI inspection buffers.
# [>] EXECUTING FLAT PATH RENDERING
def render_flat(target: Any, buffer: list[str]) -> None:
    """
    Unrolls the target data structure into flat paths and serializes them into the render buffer.

    Args:
        target (Any): The sanitized data node to trace and flatten.
        buffer (list[str]): The output string buffer to append formatted lines to.
    """
    # FLAT PATH TRACING & ITERATION
    # Unrolls the pruned target structure into flat (path, value) tuples via the tracer engine.
    traced_paths: list[tuple[str, Any]] = trace(target)

    # ENTRY FORMATTING & BUFFER POPULATION
    # Iterates through each traced path-value pair, formatting the entry with a left-aligned
    # path column and a JSON-serialized representation of the leaf value.
    for p, v in traced_paths:
        buffer.append(f"{p:<55} | {json.dumps(v)}")


# DATA CONTAINER SUBSYSTEM: DASHBOARD TABULAR RENDERER & CONTRACT MAPPER
# This utility transforms target data structures into aligned tabular dashboard views
# based on a defined field contract, computing dynamic column widths and formatting rows for CLI display.
# [>] EXECUTING DASHBOARD TABULAR RENDERING
def render_dashboard(
    target: Any, buffer: list[str], contract: dict[str, str], path: str
) -> None:
    """
    Renders structured tabular dashboard views based on a field contract map.

    Args:
        target (Any): The sanitized data node (dictionary or list) to render.
        buffer (list[str]): The output string buffer to append formatted dashboard rows to.
        contract (dict[str, str]): A mapping of display labels to object sub-keys.
        path (str): The target data path used for status logging and error reporting.
    """
    # ROW EXTRACTION & NORMALIZATION
    # Converts target dictionaries or sequences into indexed row entries, filtering out
    # non-dictionary items to establish a valid tabular data contract.
    rows: list[tuple[Any, Any]] = (
        list(cast(dict[str, Any], target).items())
        if isinstance(target, dict)
        else list(enumerate(cast(list[Any], target)))
    )
    valid_rows: list[tuple[str, dict[str, Any]]] = [
        (str(k), v) for k, v in rows if isinstance(v, dict)
    ]

    # VALID ROW EXISTENCE VALIDATION
    # Reports an informational status and exits early if no displayable dictionary objects
    # are found at the target path location.
    if not valid_rows:
        report_status(
            state="info",
            message=f"No displayable objects found at path {path!r}.",
            log_path=log_path,
        )
        return

    # DYNAMIC COLUMN WIDTH COMPUTATION
    # Calculates the maximum character width required for ID headers and each contract field label
    # by evaluating all candidate row values and label lengths.
    col_widths: dict[str, int] = {"ID": max(len(r[0]) for r in valid_rows)}
    for label, sub_key in contract.items():
        max_val: int = max(
            [len(str(r[1].get(sub_key, ""))) for r in valid_rows] + [len(label)]
        )
        col_widths[label] = max_val

    # TABULAR ROW FORMATTING & BUFFER POPULATION
    # Formats each valid row entry using calculated column widths and appends the resulting
    # structured string line to the output buffer.
    for key, item in valid_rows:
        row_output: str = f"ID: {key:<{col_widths['ID']}}"
        for label, sub_key in contract.items():
            val: Any = item.get(sub_key, "N/A")
            row_output += f" | {label}: {str(val):<{col_widths[label]}}"
        buffer.append(row_output)
