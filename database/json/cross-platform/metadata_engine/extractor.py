from typing import Any, cast


# DATA CONTAINER SUBSYSTEM: SOURCE VALUE EXTRACTION & ALIAS ROUTING
# This utility extracts values from nested source data structures using alias-prefixed dot-notation
# and deep lookups (supporting both dictionaries and numeric list indices), falling back to
# top-level keys or literal values if no alias is present.
# [>] EXECUTING SOURCE VALUE EXTRACTION
def extract_source_value(sources: dict[str, Any], source_path: str) -> Any:
    """
    Extracts value from nested source structures using dot-notation, deep lookups,
    and list index parsing.

    Args:
        sources (dict[str, Any]): A dictionary mapping source aliases to respective data pools.
        source_path (str): The dot-notated source path string including an optional source alias prefix.

    Returns:
        Any: The resolved source value, or the raw source path as a literal fallback if not found.
    """
    # ALIAS-PREFIXED PATH PARSING & DEEP LOOKUP
    # Checks if the source path contains an alias delimiter, splitting into source alias
    # and sub-path to query the specific source pool via safe iterative traversal.
    if "." in source_path:
        alias, sub_path = source_path.split(".", 1)
        current_val: Any = sources.get(alias, {})

        # ITERATIVE NESTED TRAVERSAL (DICTIONARIES & LIST INDICES)
        # Traverses sub-path segments, supporting dictionary keys as well as numeric
        # array indices (e.g., 'tracks.0.codec').
        for part in sub_path.split("."):
            if isinstance(current_val, dict):
                current_val = cast(dict[str, Any], current_val).get(part)
            elif isinstance(current_val, list) and part.isdigit():
                idx: int = int(part)
                current_list = cast(list[Any], current_val)
                current_val = current_list[idx] if idx < len(current_list) else None
            else:
                # Path resolution failed mid-traversal; treat as missing.
                current_val = None
                break
        return current_val
    else:
        # TOP-LEVEL FALLBACK & LITERAL RESOLUTION
        # Falls back to looking up top-level keys or returning the source path string as a literal value.
        return sources.get(source_path, source_path)
