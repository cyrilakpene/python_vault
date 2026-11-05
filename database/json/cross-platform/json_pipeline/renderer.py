import json
from typing import Any, cast

from .sanitizer import trace  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


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


# DATA CONTAINER SUBSYSTEM: DASHBOARD TABULAR & VERTICAL RECORD RENDERER
# This utility transforms target data structures into aligned tabular dashboard views
# or vertical key-value lists based on a defined field contract, computing dynamic
# widths and formatting rows or fields for CLI display with width capping and list formatting.
# [>] EXECUTING DASHBOARD & VERTICAL RECORD RENDERING
def render_dashboard(
    target: Any, buffer: list[str], contract: dict[str, str], path: str
) -> None:
    """
    Renders structured tabular dashboard views or vertical key-value layouts based on a field contract map,
    formatting lists cleanly and enforcing a maximum width cap with ellipsis.

    Args:
        target (Any): The sanitized data node (dictionary or list) to render.
        buffer (list[str]): The output string buffer to append formatted lines to.
        contract (dict[str, str]): A mapping of display labels to object sub-keys.
        path (str): The target data path used for status logging and error reporting.
    """
    # SINGLE RECORD DETECTION & VERTICAL LINE-BY-LINE RENDERING
    # Dynamically verifies whether the target dictionary represents a single entity record
    # (where nested dictionaries are exclusively domain metadata groups rather than child rows).
    is_single_record = False
    if isinstance(target, dict):
        target_dict = cast(dict[Any, Any], target)
        # Generic heuristic: Extract base property keys from the contract mapping
        # to determine if the dictionary represents a single entity's attributes
        # rather than a collection container mapping IDs to record dictionaries.
        contract_base_keys = {
            sub_key.split(".")[0].split("[")[0] for sub_key in contract.values()
        }

        # A dictionary is a single record if its keys intersect with the contract
        # schema or if it contains non-dictionary attributes (scalars/lists).
        has_contract_keys = any(k in target_dict for k in contract_base_keys)
        all_values_are_dicts = bool(target_dict) and all(
            isinstance(v, dict) for v in target_dict.values()
        )

        is_single_record = has_contract_keys or not all_values_are_dicts

    if isinstance(target, dict) and is_single_record:
        # Compute maximum label length for clean vertical colon alignment
        max_label_len: int = (
            max(len(label) for label in contract.keys()) if contract else 0
        )

        for label, sub_key in contract.items():
            # Resolve dot-notation keys (e.g., 'staff.director[0]' or 'attributes.season') safely
            val: Any = cast(dict[Any, Any], target)
            for part in sub_key.replace("[", ".").replace("]", "").split("."):
                if isinstance(val, dict):
                    val = cast(dict[Any, Any], val).get(part, "N/A")
                elif isinstance(val, list) and part.isdigit():
                    idx: int = int(part)
                    items: list[Any] = cast(list[Any], val)
                    val = items[idx] if idx < len(items) else "N/A"
                else:
                    val = "N/A"
                    break

            if val is None:
                val = "N/A"

            # LIST FORMATTING: REMOVING BRACKETS
            # If the resolved value is a list, format it into a clean comma-separated string without brackets.
            if isinstance(val, list):
                val_str = ", ".join(str(item) for item in cast(list[Any], val))
            else:
                val_str = str(val)

            # WIDTH CAPPING & ELLIPSIS ENFORCEMENT
            # Limits the formatted line structure to a max width of 74 characters, appending '...' if truncated.
            line_prefix = f"{label:<{max_label_len}} : "
            max_val_width = 74 - len(line_prefix)

            if len(val_str) > max_val_width and max_val_width > 3:
                val_str = val_str[: max_val_width - 3] + "..."

            buffer.append(f"    {line_prefix} {val_str}")
        return

    # ROW EXTRACTION & NORMALIZATION FOR COLLECTIONS
    # Handles multi-row datasets (lists or dictionaries of multiple entity records).
    valid_rows: list[tuple[str, dict[str, Any]]] = []

    if isinstance(target, dict):
        rows = list(cast(dict[Any, Any], target).items())
        valid_rows = [
            (str(k), cast(dict[str, Any], v)) for k, v in rows if isinstance(v, dict)
        ]
    elif isinstance(target, list):
        rows = list(enumerate(cast(list[Any], target)))
        valid_rows = [
            (str(k), cast(dict[str, Any], v)) for k, v in rows if isinstance(v, dict)
        ]

    # VALID ROW EXISTENCE VALIDATION
    # Reports an informational status and exits early if no displayable dictionary objects
    # are found at the target path location.
    if not valid_rows:
        report_status(
            state="info",
            message=f"No displayable objects found at path {path!r}.",
            context=LogContext(
                component="database.JSONDatabasePipeline",
                log_path=log_path,
                silent=False,
                trace_id="JSONDatabasePipeline",
                actor=context.get("user"),
                payload={"path": path},
            ),
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

        # Enforce 84-character width cap on tabular rows as well
        if len(row_output) > 84:
            row_output = row_output[:81] + "..."

        buffer.append(row_output)
