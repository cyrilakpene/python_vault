import re
import json
from typing import Any, Callable, Literal, cast

from .sanitizer import clean_data, sanitize  # type: ignore[import-not-found]
from .renderer import render_flat, render_dashboard  # type: ignore[import-not-found]
from .constants import report_status, log_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: PATH-BASED DATA RETRIEVAL & DYNAMIC QUERY ENGINE
# This method serves as the primary safe navigation interface for fetching deeply nested data
# using a tokenized path protocol. It abstracts physical structures, supporting dictionary keys,
# integer indexing, and predicate-based sequence matching (e.g., 'series[name=Oshi No Ko]')
# with robust null-pointer protection and exception shielding.
# [>] EXECUTING PATH-BASED DATA RETRIEVAL & QUERY
def get_data(data: Any, path: str) -> Any | None:
    """
    Retrieves data using a normalized path protocol.

    Leverages tokenized paths from the sanitizer to navigate dictionaries and lists.
    This iteration-based approach prevents recursion-depth errors and ensures safe 'None'
    returns on missing nodes or traversal mismatches.

    Args:
        data (Any): The data structure to query.
        path (str): The target dot-notation or predicate query path.

    Returns:
        Any | None: The resolved data value, or None if the path does not exist.
    """
    # INBOUND PATH TOKENIZATION
    # Transform the string path into normalized navigational tokens via the grammar engine.
    keys: list[str] = sanitize(path)
    val: Any = data

    # ITERATIVE TREE TRAVERSAL
    # Traverse the JSON tree node by node using iteration rather than recursive stack frames.
    for key in keys:
        # FAIL-FAST: NULL-POINTER PROTECTION
        # Prevent 'NoneType' subscripting by halting traversal immediately if a parent node resolves to None.
        if val is None:
            return None

        try:
            # DYNAMIC DISPATCH (PREDICATE VS INDEX VS DICT KEY)
            # Handle predicate-based property searching for lists (e.g., 'list_key[attr=val]').
            if "[" in key and "=" in key:
                match: re.Match[str] | None = re.match(r"(.+)\[(.+)=(.+)\]", key)
                if match:
                    list_key, attr, target_val = match.groups()
                    candidate: Any = (
                        cast(dict[str, Any], val).get(list_key)
                        if isinstance(val, dict)
                        else None
                    )
                    items: list[Any] = []
                    if isinstance(candidate, list):
                        items = cast(list[Any], candidate)

                    # PREDICATE-BASED SEQUENCE SEARCH
                    # Locate the first matching dictionary item where the attribute equals target_val.
                    val = next(
                        (
                            cast(dict[str, Any], item)
                            for item in items
                            if isinstance(item, dict)
                            and str(cast(dict[str, Any], item).get(attr)) == target_val
                        ),
                        None,
                    )
                else:
                    return None

            # TYPE-SAFE SEQUENCE INDEXING
            # Perform bounds-checked index lookup if current node is a list and key is numeric.
            elif isinstance(val, list) and key.isdigit():
                idx: int = int(key)
                items = cast(list[Any], val)
                val = items[idx] if idx < len(items) else None

            # ENCAPSULATED DICTIONARY LOOKUP
            # Perform standard dictionary key retrieval using .get() to prevent KeyErrors.
            elif isinstance(val, dict):
                val = cast(dict[str, Any], val).get(key)

            else:
                # BLOCKING ILLEGAL TRAVERSAL
                # Terminate if traversal attempts to index primitive types as maps.
                return None

        # EXCEPTION SHIELDING & ERROR RECOVERY
        # Catch indexing, casting, or type errors and return None safely instead of crashing.
        except (IndexError, TypeError, ValueError):
            return None

    return val


# DATA CONTAINER SUBSYSTEM: HIGH-LEVEL CLI INSPECTOR & DYNAMIC FRAMING ENGINE
# This utility acts as the primary inspection interface for querying and rendering data paths
# in flat key-value formats, raw JSON schemas, or customized dashboard layouts with dynamic symmetry.
# [>] EXECUTING CLI PATH INSPECTION & RENDERING
def print_path(
    data: Any, path: str, view: Literal["flat", "json"] | dict[str, str] = "flat"
) -> None:
    """
    High-level CLI inspector with dynamic width framing.

    Args:
        data (Any): The data structure to inspect.
        path (str): Dot-notated string targeting specific nodes within the internal state.
        view (Literal["flat", "json"] | dict[str, str], optional): Output format control. Defaults to "flat".
    """
    # DATA ACQUISITION & PATH TARGETING
    # Retrieves the target node using path resolution, reporting a failure status and returning early
    # if the path does not exist in the state.
    raw_target: Any = get_data(data, path)

    if raw_target is None:
        report_status(
            state="fail",
            message=f"Path {path!r} not found in the current state.",
            log_path=log_path,
        )
        return

    # METADATA PRUNING & INSPECTION LOGGING
    # Sanitizes the target node via the metadata firewall and logs the active inspection configuration.
    target: Any = clean_data(raw_target)
    report_status(
        state="info",
        message=f"Inspecting path {path!r} with view mode {view!r}.",
        log_path=log_path,
    )

    # RAW JSON STRUCTURAL VIEW MODE (THE ARCHITECT'S VIEW)
    # Serializes and prints the pruned data structure as formatted JSON if json view mode is selected.
    if view == "json":
        print(json.dumps(target, indent=2))
        return

    buffer: list[str] = []

    # DICTIONARY DISPATCH REGISTRY (LAMBDA WRAPPED FOR DEFERRED EXECUTION)
    # Maps view identifiers to their respective rendering strategy callables,
    # ensuring target and buffer arguments are passed dynamically at execution time.
    view_dispatch: dict[str, Callable[[Any, list[str]], None]] = {
        "flat": lambda t, b: render_flat(t, b),
    }

    # VIEW STRATEGY RESOLUTION & EXECUTION
    # Dispatches rendering to either the flat path tracer or the custom dashboard layout engine
    # based on the specified view parameter type.
    if isinstance(view, str):
        handler = view_dispatch.get(view)
        if handler:
            handler(target, buffer)
    else:
        render_dashboard(target, buffer, view, path)

    # DYNAMIC SYMMETRY ENGINE & HORIZONTAL FRAMING
    # Computes maximum line width across rendered buffer items and prints a symmetrically framed
    # terminal output block bounded by horizontal separator rules.
    if buffer:
        actual_width: int = max(len(line) for line in buffer)
        print("-" * actual_width)
        for line in buffer:
            print(line)
        print("-" * actual_width)


# DATA CONTAINER SUBSYSTEM: EXPLORATION API & DATA ARCHITECTURE DISCOVERY
# This method provides a clean API-like surface for navigating the JSON structure by retrieving
# a list of functional keys at a specified path. It automatically prunes internal documentation keys
# (prefixed with '//_') to provide a production-ready view of the schema.
# [>] EXECUTING KEY DISCOVERY & EXPLORATION
def get_keys(data: Any, path: str = "") -> list[str]:
    """
    Retrieves a list of functional keys at a specified path.

    Args:
        data (Any): The data structure to query.
        path (str, optional): The starting node path for exploration. Defaults to "" (root).

    Returns:
        list[str]: A list of non-documentation functional keys residing at the target node.
    """
    # TARGET NODE IDENTIFICATION
    # Determine the root or specific branch for key inspection; default to entire data state if path is empty.
    target: Any = data if path == "" else get_data(data, path)

    # TYPE-SAFE ITERATION & DOCUMENTATION FILTERING
    # Verify the target is a dictionary and return all keys excluding those prefixed with '//_',
    # separating human metadata from machine data.
    if isinstance(target, dict):
        target_dict = cast(dict[str, Any], target)
        return [key for key in target_dict.keys() if not key.startswith("//_")]

    # FALLBACK FOR NON-NAVIGABLE NODES
    # Return an empty list if the target is a sequence or primitive leaf node where keys cannot be extracted.
    return []
