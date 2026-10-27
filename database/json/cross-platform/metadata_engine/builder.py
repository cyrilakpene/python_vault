import copy
from typing import Any, cast


# DATA CONTAINER SUBSYSTEM: TREE COMMITMENT & ADVANCED LIST/BRANCH COLLISION GUARD
# This utility inserts values into the target tree hierarchy using dot-notation paths,
# supporting both dictionary mapping and index-safe list padding/construction.
# [>] EXECUTING TREE VALUE COMMITMENT
def commit_value_to_tree(
    final_dict: dict[str, Any], target_path: str, value: Any
) -> None:
    """
    Inserts a value into the target tree with collision guards and support for
    nested lists, index padding, and dictionary branches.

    Args:
        final_dict (dict[str, Any]): The target dictionary tree being constructed.
        target_path (str): The dot-notated destination path string (supporting list indices like 'streams.0.codec').
        value (Any): The value or collection payload to commit.

    Raises:
        TypeError: If a branch node type mismatch occurs or terminal keys collide.
    """
    # DEEP-PATH ISOLATION: IMMUTABILITY ENFORCEMENT
    # We decouple the inbound value from its source buffer. By utilizing 'deepcopy'
    # for complex mutable types (dicts and lists), we prevent upstream pointer-sharing
    # or accidental mutations from corrupting our synthesized clean state[cite: 1].
    # [>] SECURING DATA INTEGRITY
    value_to_commit = (
        copy.deepcopy(cast(Any, value)) if isinstance(value, (dict, list)) else value
    )

    target_parts: list[str] = target_path.split(".")
    cursor: Any = final_dict

    # RECURSIVE BRANCH ALLOCATION: HIERARCHY SYNTHESIS & LOOK-AHEAD
    # We iterate through all path segments except the terminal 'Leaf'. This phase builds
    # the skeletal structure of the tree, utilizing a 'Look-Ahead' to forecast whether
    # the next node requires a dictionary container or an indexed sequence.
    # [>] CONSTRUCTING INTERMEDIATE NODES
    for i, node in enumerate(target_parts[:-1]):
        next_part = target_parts[i + 1]

        # LOOK-AHEAD PROBE: TOPOLOGICAL FORECAST FOR LISTS
        # Checks if the subsequent segment is numeric to dynamically handle list indices
        # and bridge the structural gap between mappings and sequences[cite: 8].
        # [>] EVALUATING BRANCH AFFINITY
        if next_part.isdigit():
            if isinstance(cursor, dict):
                cursor_dict = cast(dict[str, Any], cursor)
                # [>] INITIALIZING/VALIDATING LIST BRANCH
                if node not in cursor_dict:
                    cursor_dict[node] = []
                elif not isinstance(cursor_dict[node], list):
                    # SYMBOLIC STATUS: TOPOLOGICAL COLLISION
                    raise TypeError(
                        f"Schema Collision: Node '{node}' is expected to be a list branch."
                    )
                target_list = cast(list[Any], cursor_dict[node])
            elif isinstance(cursor, list):
                cursor_list = cast(list[Any], cursor)
                idx_node = int(node)
                # LIST EXPANSION: INDEX-SAFE PADDING
                # Pads the parent list with None to prevent IndexError crashes during sparse navigation.
                while len(cursor_list) <= idx_node:
                    cursor_list.append(None)
                if cursor_list[idx_node] is None:
                    cursor_list[idx_node] = []
                target_list = cursor_list[idx_node]
            else:
                raise TypeError(
                    f"Schema Collision: Invalid container type during traversal."
                )

            idx = int(next_part)

            # LIST EXPANSION: INDEX-SAFE PADDING (TARGET SEQUENCE)
            # Pads the target list with None values to ensure the target index exists.
            # [>] EXPANDING LIST HORIZON
            while len(target_list) <= idx:
                target_list.append(None)

            # BRANCH DEPTH EVALUATION: CURSOR ADVANCEMENT
            # Resolves nested depth to instantiate the correct container within the list index.
            # [>] PROJECTING NESTED DEPTH
            if i < len(target_parts) - 2:
                is_next_next_list = target_parts[i + 2].isdigit()
                if target_list[idx] is None:
                    target_list[idx] = [] if is_next_next_list else {}
                cursor = target_list[idx]
            else:
                cursor = target_list
        else:
            # DICTIONARY BRANCH TRAVERSAL & COLLISION CHECK
            # Standard dictionary logic for non-numeric path segments, enforcing schematic consistency.
            # [!] EVALUATING NODE TOPOLOGY
            if isinstance(cursor, dict):
                cursor_dict = cast(dict[str, Any], cursor)
                if node in cursor_dict and not isinstance(cursor_dict[node], dict):
                    # SYMBOLIC STATUS: LEAF-BRANCH COLLISION
                    raise TypeError(
                        f"Schema Collision: Path node '{node}' is already a "
                        f"Value and cannot be transformed into a Branch[cite: 1]."
                    )
                if node not in cursor_dict:
                    cursor_dict[node] = {}
                cursor = cursor_dict[node]
            elif isinstance(cursor, list):
                cursor_list = cast(list[Any], cursor)
                idx_node = int(node)
                while len(cursor_list) <= idx_node:
                    cursor_list.append(None)
                if cursor_list[idx_node] is None:
                    cursor_list[idx_node] = {}
                cursor = cursor_list[idx_node]

    last_key: str = target_parts[-1]

    # FINAL VALUE COMMITMENT: LEAF PROMOTION & COLLISION GUARD
    # Assigns the value to the terminal key or index, verifying top-level container integrity
    # to protect the synthesized structure from flattening or corruption[cite: 8].
    # [>] RESOLVING TERMINAL NODE
    if last_key.isdigit():
        idx_final = int(last_key)
        if not isinstance(cursor, list):
            raise TypeError(
                f"Schema Collision: Terminal parent is not a list, cannot assign index '{last_key}'."
            )
        cursor_list = cast(list[Any], cursor)
        while len(cursor_list) <= idx_final:
            cursor_list.append(None)
        # [+] COMMITTING STATE: INDEXED ASSIGNMENT
        cursor_list[idx_final] = value_to_commit
    else:
        if isinstance(cursor, dict):
            # LEAF-BRANCH VALIDATION: TOPOLOGICAL INTEGRITY
            if last_key in cursor and isinstance(cursor[last_key], (dict, list)):
                # SYMBOLIC STATUS: TERMINAL COLLISION
                raise TypeError(
                    f"Schema Collision: Terminal key '{last_key}' is already "
                    f"defined as a Branch and cannot be overwritten by a Value[cite: 1]."
                )
            # COMMITTING STATE: ATOMIC WRITE
            cursor[last_key] = value_to_commit
        else:
            raise TypeError(
                f"Schema Collision: Terminal parent is not a dictionary, cannot assign key '{last_key}'."
            )


# DATA CONTAINER SUBSYSTEM: EMPTY BRANCH SCRUBBING & SKELETON PRUNING
# This utility recursively traverses data structures to clean up and prune empty skeleton
# dictionary branches resulting from null-stripping operations.
# [>] EXECUTING EMPTY BRANCH SCRUBBING
def scrub_empty_branches(node: Any) -> Any:
    """
    Recursively cleans up empty skeleton dictionary branches resulting from null-stripping.

    Args:
        node (Any): The node, collection, or dictionary tree to scrub.

    Returns:
        Any: The pruned node or cleaned dictionary structure with empty branches removed.
    """
    # NON-DICTIONARY PASS-THROUGH
    # Returns the node directly if it is not a dictionary container.
    if not isinstance(node, dict):
        return node

    # RECURSIVE CHILD SCRUBBING
    # Recursively applies the scrubbing operation across all child dictionary key-value pairs.
    typed_node = cast(dict[str, Any], node)
    cleaned_node: dict[str, Any] = {
        k: scrub_empty_branches(v) for k, v in typed_node.items()
    }

    # EMPTY SKELETON PRUNING
    # Filters out child entries that evaluate to empty dictionaries after recursive cleaning,
    # assembling the final pruned result dictionary.
    result: dict[str, Any] = {}
    for key, value in cleaned_node.items():
        if isinstance(value, dict) and not value:
            continue
        result[key] = value
    return result
