import re
from typing import Any, Iterable, cast


# DATA CONTAINER SUBSYSTEM: RECURSIVE VIRTUAL PATH RESOLUTION
# This utility resolves complex, multi-nested query paths with bracketed predicates (e.g., [id=123])
# into static virtual pointers, enabling dynamic filtering during metadata synthesis.
# [>] EXECUTING VIRTUAL PATH RESOLUTION
def resolve_query_paths(
    sources: dict[str, Any], mapping_registry: dict[str, str]
) -> tuple[dict[str, Any], dict[str, str]]:
    """
    Resolves complex, multi-nested query paths into static pointers using iterative reduction
    and bracketed predicate matching.

    Args:
        sources (dict[str, Any]): A dictionary of raw input data buffers.
        mapping_registry (dict[str, str]): The source-to-target mapping registry.

    Returns:
        tuple[dict[str, Any], dict[str, str]]: The augmented data pool with virtual injections
        and the sanitized registry.
    """
    # REGEX COMPILATION & PATTERN DEFINITION
    # Defines the pattern to capture upstream paths, target keys, predicates, and remainders.
    bracket_pattern = r"(.*?)\.?([\w\d_-]+)\[([\w\d_-]+)=([\w\d_-]+)\](.*)"

    # WORKSPACE INITIALIZATION & BUFFER CLONING
    # Initializes the working copies of the data sources and output mapping registry.
    resolved_sources = sources.copy()
    resolved_registry: dict[str, str] = {}

    # MAPPING REGISTRY ITERATION & PATH EVALUATION LOOP
    # Iterates through each source-to-target mapping entry to evaluate and resolve paths.
    for source_path, target_path in mapping_registry.items():
        current_working_path = source_path
        resolution_chain_broken = False

        # THE RESOLUTION LOOP: REWRITING PATHS FOR MULTI-DEPTH QUERIES
        # Continues resolving bracketed query predicates as long as they exist in the path.
        while "[" in current_working_path:
            match = re.search(bracket_pattern, current_working_path)

            # REGEX MATCH VALIDATION CHECK
            # Breaks the resolution chain if the path syntax fails to match the bracket pattern.
            if not match:
                resolution_chain_broken = True
                break

            prefix, list_key, q_key, q_val, remainder = match.groups()

            # BUFFER ACCESS: NAVIGATING THE HIERARCHY
            # Traverses the nested source dictionary structure based on the extracted prefix.
            search_area: Any = resolved_sources
            if prefix:
                for part in prefix.strip(".").split("."):
                    if part:
                        if isinstance(search_area, dict) and part in search_area:
                            search_area = cast(Any, search_area[part])
                        else:
                            resolution_chain_broken = True
                            break

                    if resolution_chain_broken:
                        break

            if resolution_chain_broken:
                break

            # ISOLATING TARGET COLLECTION
            # Verifies and isolates the target collection sequence or dictionary container.
            if isinstance(search_area, dict) and list_key in search_area:
                target_sequence = cast(Any, search_area[list_key])
            else:
                resolution_chain_broken = True
                break

            # PREDICATE MATCHING & NORMALIZATION
            # Normalizes the target query value for case-insensitive matching against collection items.
            target_val_clean = str(q_val).strip().lower()
            items_to_scan = cast(
                Iterable[Any],
                (
                    target_sequence.values()
                    if isinstance(target_sequence, dict)
                    else target_sequence
                ),
            )

            # ITERATIVE ITEM SCANNING & PREDICATE EVALUATION
            # Scans through collection items to locate the exact dictionary matching the predicate.
            found_item: dict[str, Any] | None = None
            for item in items_to_scan:
                if isinstance(item, dict):
                    item_dict = cast(dict[str, Any], item)
                    actual_val = str(item_dict.get(q_key)).strip().lower()
                    if actual_val == target_val_clean:
                        found_item = cast(dict[str, Any], item)
                        break

            if found_item:
                # VIRTUAL INJECTION: ROOT-LEVEL PINNING
                # Generates a unique virtual pointer and injects the matched item into root sources.
                v_id = f"v_res_{len(resolved_sources)}"
                resolved_sources[v_id] = found_item

                # PATH RECONCILIATION & FRAGMENT RE-ASSEMBLY
                # Reconstructs the working path using the new virtual root pointer and remainder.
                remainder = remainder.lstrip(".")
                current_working_path = f"{v_id}.{remainder}" if remainder else v_id
            else:
                resolution_chain_broken = True
                break

        # REGISTERING RESOLVED POINTER OR FALLBACK PATH
        # Commits the successfully resolved virtual path or falls back to the original source path.
        if not resolution_chain_broken:
            resolved_registry[current_working_path] = target_path
        else:
            resolved_registry[source_path] = target_path

    # RESOLUTION MANIFEST RETURN
    # Returns the augmented data sources dictionary and the updated mapping registry.
    return resolved_sources, resolved_registry
