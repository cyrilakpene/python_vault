import re
from typing import Any, cast


# DATA CONTAINER SUBSYSTEM: RECURSIVE DATA PRUNING & METADATA STRIPPING
# This internal method implements a depth-first traversal of the object tree to sanitize payloads
# for machine consumption by stripping internal documentation keys (prefixed with '//_'), acting
# as a heuristic firewall that separates human-readable metadata from machine-ready data.
# [>] EXECUTING DATA PRUNING & METADATA SANITIZATION
def clean_data(object: Any) -> Any:
    """
    Recursively prunes documentation keys (prefixed with //_).

    JSON structures are tree-like with arbitrary depth. Recursion is the only reliable way
    to traverse these nodes, separating human-readable metadata from machine-ready data.

    Args:
        object (Any): The data object (dictionary, list, or primitive leaf) to be sanitized.

    Returns:
        Any: The cleaned and pruned data structure.
    """
    # DICTIONARY TRAVERSAL & KEY FILTERING
    # If the input is a dictionary, rebuild it using a comprehension that discards any keys
    # prefixed with '//_' while recursively cleaning all nested values.
    if isinstance(object, dict):
        return {
            k: clean_data(v)
            for k, v in cast(dict[Any, Any], object).items()
            if not (isinstance(k, str) and k.startswith("//_"))
        }

    # SEQUENCE PROCESSING
    # If the input is a list, process each element recursively to guarantee schema integrity
    # across all nested array nodes.
    elif isinstance(object, list):
        return [clean_data(i) for i in cast(list[Any], object)]

    # BASE TYPE PRESERVATION (LEAF NODES)
    # Return primitive data types (strings, integers, floats, booleans, None) as-is,
    # preventing infinite recursion at the leaves of the object tree.
    return object


# DATA CONTAINER SUBSYSTEM: PATH TOKENIZATION & SEMANTIC NORMALIZATION
# This method acts as the grammar engine for the pipeline, transforming raw string paths into
# a clean sequence of navigational tokens by resolving bracket-notation, stripping whitespace,
# and filtering structural noise to ensure robust traversal across dictionaries and lists.
# [>] EXECUTING PATH TOKENIZATION & NORMALIZATION
def sanitize(path: str) -> list[str]:
    """
    Tokenizes the path protocol, resolving dots and bracket-notation.

    Args:
        path (str): The raw string path (e.g., 'metadata.series[0].id') to tokenize.

    Returns:
        list[str]: A sequence of clean, sequential navigational tokens representing targeted nodes.
    """
    # STRUCTURAL NOISE REDUCTION
    # Strip leading and trailing whitespace to prevent lookup failures caused by CLI formatting
    # artifacts or manual input typos before path processing begins.
    path = path.strip()

    # BRACKET-TO-DOT NORMALIZATION
    # Transform array bracket-notation (e.g., 'series[0]') into dot-notation ('series.0')
    # using regular expressions to unify dict and list traversal under a single tokenized flow.
    normalized_path: str = re.sub(r"\[(\d+)\]", r".\1", path)

    # TOKEN EXTRACTION & VOID FILTERING
    # Split by '.' and filter out empty strings to prevent traversal breaches from malformed
    # paths (e.g., 'metadata..id'), guaranteeing the pipeline navigates only valid structural nodes.
    tokens: list[str] = [t for t in normalized_path.split(".") if t]

    # VALIDATED TOKEN STREAM RETURN
    # Return the clean, sequential map of targeted JSON nodes ready for traversal.
    return tokens


# DATA CONTAINER SUBSYSTEM: RECURSIVE PATH DECONSTRUCTION & IDENTITY PROMOTION
# This internal method performs a deep-walk of nested data structures, unrolling dictionaries
# and lists into flat `(Path, Value)` tuples. It implements identity promotion by resolving
# signature keys ('name' or 'id') into stable predicate query paths rather than volatile array indices.
# [>] EXECUTING RECURSIVE PATH DECONSTRUCTION
def trace(data: Any, current_path: str = "") -> list[tuple[str, Any]]:
    """
    Unrolls nested data into (Path, Value) tuples.

    Supports dictionary traversal and predicate-based list identification. If a list item contains
    a 'name' or 'id', it constructs the '[attr=val]' syntax instead of a raw index to ensure
    the path remains query-stable across dataset shifts.

    Args:
        data (Any): The data node to deconstruct.
        current_path (str, optional): The accumulated path string from parent nodes. Defaults to "".

    Returns:
        list[tuple[str, Any]]: A flat list of resolved dot-predicate paths and their leaf values.
    """
    paths: list[tuple[str, Any]] = []

    # DICTIONARY TRAVERSAL & HIERARCHY EXPANSION
    # Append keys to the current path using dot-notation, recursively traversing down
    # the metadata tree structure.
    if isinstance(data, dict):
        for key, value in cast(dict[str, Any], data).items():
            new_path: str = f"{current_path}.{key}" if current_path else str(key)
            paths.extend(trace(value, new_path))

    # LIST INDEXING & STABLE IDENTITY PROMOTION
    # Evaluate list elements for signature anchors ('name' or 'id') to promote volatile numeric
    # indices to robust predicate-based paths (e.g., 'series[name=Example]'), ensuring archival stability.
    elif isinstance(data, list):
        for i, item in enumerate(cast(list[Any], data)):
            identity: str | int | None = None
            attr_key: str | None = None

            if isinstance(item, dict):
                item_dict = cast(dict[str, Any], item)
                name_value = item_dict.get("name")
                if isinstance(name_value, (str, int)):
                    identity = name_value
                    attr_key = "name"
                else:
                    id_value = item_dict.get("id")
                    if isinstance(id_value, (str, int)):
                        identity = id_value
                        attr_key = "id"

            # PATH SUFFIX RESOLUTION (PREDICATE VS. NUMERIC INDEX)
            # Utilize bracket-predicate notation if stable identity is found; otherwise, fall back
            # to standard integer indexing `[i]` to maintain complete structural coverage.
            if identity is not None:
                suffix: str = f"[{attr_key}={identity}]"
            else:
                suffix = f"[{i}]"

            paths.extend(trace(item, f"{current_path}{suffix}"))

    # TERMINAL LEAF EMISSION
    # Once a primitive leaf node is reached (string, int, float, bool, None), append the accumulated
    # path and its final value to the flat path collection.
    else:
        paths.append((current_path, data))

    return paths


# DATA CONTAINER SUBSYSTEM: DEEP VALUE RESOLUTION & SIMPLIFIED PATH LOOKUP
# This utility provides a lightweight traversal mechanism to extract values from nested dictionaries
# using dot-separated path strings, supporting direct value pass-through for non-string paths.
# [>] EXECUTING DEEP VALUE RESOLUTION
def get_deep_value(data: Any, path: str | Any) -> Any:
    """
    Retrieves a nested value using a simple dot-separated path string.

    Args:
        data (Any): The data structure (dictionary or nested maps) to query.
        path (str | Any): The dot-separated path string or a direct value to return as-is.

    Returns:
        Any: The resolved value, the raw path object if non-string, or None if a node is missing.
    """
    # PATH TYPE VERIFICATION (DIRECT PASS-THROUGH)
    # Returns the path argument directly if it is not a string, bypassing lookup overhead.
    if not isinstance(path, str):
        return path

    # PATH TOKENIZATION & INITIALIZATION
    # Splits the path string by dots into navigational keys and sets the traversal pointer to root data.
    keys: list[str] = path.split(".")
    val: Any = data

    # ITERATIVE DICTIONARY TRAVERSAL
    # Iterates through each key, stepping down into nested dictionaries or returning None
    # if a non-dictionary node is encountered mid-traversal.
    for key in keys:
        if isinstance(val, dict):
            val = cast(dict[str, Any], val).get(key)
        else:
            return None

    return val


# DATA CONTAINER SUBSYSTEM: DYNAMIC BRANCH RESOLUTION & SCHEMA MAPPING
# This utility recursively resolves schema templates against a data pool, constructing
# structured output branches by mapping nested dictionaries, lists, and path expressions
# using deep value lookup routines.
# [>] EXECUTING BRANCH RESOLUTION & SCHEMA MAPPING
def resolve_branch(
    current_schema: dict[str, Any], data_pool: dict[str, Any]
) -> dict[str, Any]:
    """
    Recursively resolves a schema template against a data pool.

    Args:
        current_schema (dict[str, Any]): The schema template defining target structure and lookup paths.
        data_pool (dict[str, Any]): The source data repository containing values to ingest.

    Returns:
        dict[str, Any]: The fully resolved and populated branch dictionary.
    """
    # BRANCH INITIALIZATION
    # Instantiates an empty dictionary to hold the resolved key-value pairs for the current branch level.
    branch: dict[str, Any] = {}

    # SCHEMA ITERATION & TYPE DISPATCH
    # Iterates through each schema entry, handling nested sub-schemas, lists of path lookups,
    # and primitive path expressions recursively.
    for out_key, in_val in current_schema.items():

        # NESTED DICTIONARY RECURSION
        # If the schema value is a nested dictionary, recursively resolve the sub-branch against the data pool.
        if isinstance(in_val, dict):
            branch[out_key] = resolve_branch(cast(dict[str, Any], in_val), data_pool)

        # LIST MAPPING & BATCH LOOKUP
        # If the schema value is a list, map each item through the deep value resolver to extract
        # sequence elements from the data pool.
        elif isinstance(in_val, list):
            branch[out_key] = [
                get_deep_value(data_pool, item) for item in cast(list[Any], in_val)
            ]

        # LEAF PATH EXPRESSION RESOLUTION
        # Resolves single leaf path strings or constant values directly from the data pool via deep lookup.
        else:
            branch[out_key] = get_deep_value(data_pool, in_val)

    return branch
