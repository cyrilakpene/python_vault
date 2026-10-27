from typing import Any, cast


# DATA CONTAINER SUBSYSTEM: DOT-NOTATED PATH RESOLUTION ENGINE
# This utility traverses nested dictionary structures using dot-notation path strings,
# returning the resolved value or None to represent an unset or missing state for logical gates.
# [>] EXECUTING DOT-NOTATED PATH RESOLUTION
def resolve_path(target_dict: dict[str, Any], path: str) -> Any:
    """
    Traverses a nested dictionary using dot-notation path strings.
    Returns the value if found, otherwise returns None to signify
    a 'Null' or 'Unset' state for the logical gates.

    Args:
        target_dict (dict[str, Any]): The target dictionary container to traverse.
        path (str): The dot-notated string path targeting the nested value.

    Returns:
        Any: The resolved value if found; None if any path segment is missing or invalid.
    """
    # PATH SEGMENTATION & CURSOR INITIALIZATION
    # Splits the dot-notation path string into individual parts and sets the traversal cursor
    # to the root target dictionary.
    path_parts: list[str] = path.split(".")
    current_val: Any = target_dict

    # RECURSIVE DICTIONARY TRAVERSAL
    # Iterates through each path part, stepping deeper into the dictionary container
    # if the part exists as a valid key. Returns None immediately if path breaks occur.
    for part in path_parts:
        if isinstance(current_val, dict) and part in current_val:
            current_val = cast(Any, current_val[part])
        else:
            return None

    return current_val


# DATA CONTAINER SUBSYSTEM: DOT-NOTATED PATH INJECTION & DICTIONARY MUTATION
# This utility traverses dot-notation path strings and assigns values to leaf nodes,
# automatically initializing missing intermediate dictionary branches along the way.
# [>] EXECUTING DOT-NOTATED PATH INJECTION
def inject_path(target_dict: dict[str, Any], path: str, value: Any) -> None:
    """
    Traverses a dot-notation path and assigns the provided value
    to the leaf node. Automatically initializes missing parent dicts.

    Args:
        target_dict (dict[str, Any]): The target dictionary container to inject values into.
        path (str): The dot-notated string path targeting the destination leaf node.
        value (Any): The value or collection payload to assign.

    Returns:
        None
    """
    # PATH SEGMENTATION & CURSOR INITIALIZATION
    # Splits the dot-notation path string into parts and initializes the traversal cursor
    # to the root target dictionary container.
    path_parts: list[str] = path.split(".")
    current_level = target_dict

    # INTERMEDIATE BRANCH TRAVERSAL & AUTO-INITIALIZATION
    # Iterates through parent path segments, using setdefault() to automatically
    # create and navigate missing dictionary branches.
    for part in path_parts[:-1]:
        current_level = current_level.setdefault(part, {})

    # LEAF NODE ASSIGNMENT
    # Assigns the value to the final terminal key within the resolved level.
    current_level[path_parts[-1]] = value
