from typing import Any, cast

from .model import FilterFeatures  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: RECURSIVE SCRUBBER FACTORY & ATTRIBUTE HOISTING ENGINE
# This utility acts as a factory function returning a recursive scrubber closure
# for pattern purging, exclusion filtering, target key identification, and attribute hoisting.
# [>] EXECUTING SCRUBBER FACTORY INITIALIZATION
def create_scrubber(
    patterns: list[str],
    target_keys: list[str],
    features: FilterFeatures,
    resolve_targets_func: Any,
) -> Any:
    """
    Factory that returns a recursive scrubber closure for pattern purging and attribute hoisting.

    Args:
        patterns (list[str]): A list of key prefix patterns to exclude during the cleaning pass.
        target_keys (list[str]): Specific keys targeted for logical hoisting and aggregation.
        features (dict[str, Any]): Feature flag configurations controlling global merges and strict flattening.
        resolve_targets_func (Any): Strategy function used to resolve or stabilize target outputs.

    Returns:
        Any: A recursive scrubber closure function capable of processing lists and dictionaries.
    """

    # SCRUBBER CLOSURE DEFINITION
    # Defines the internal recursive closure that traverses data structures,
    # purging matched patterns and hoisting target keys.
    def _scrubber(node: Any) -> Any:
        # LIST RECURSION & TRAVERSAL
        # Recursively processes each element if the current node is a list.
        if isinstance(node, list):
            items = cast(list[Any], node)
            return [_scrubber(item) for item in items]

        # DICTIONARY SCRUBBING & RESTRUCTURING
        # Processes dictionaries by applying pattern-based exclusion, target identification,
        # and consolidation or global merging strategies.
        if isinstance(node, dict):
            # Pattern-based exclusion (cleaning pass)
            # Filters out dictionary keys whose prefixes match any of the specified exclusion patterns.
            clean_node: dict[str, Any] = {
                k: v
                for k, v in cast(dict[str, Any], node).items()
                if not any(str(k).startswith(p) for p in patterns)
            }

            if not target_keys and not features.get("global_merge", False):
                return {k: _scrubber(v) for k, v in clean_node.items()}

            # Target key identification (logical hoisting)
            # Identifies and recursively scrubs specified target keys within the cleaned node.
            found_targets: dict[str, Any] = {
                k: _scrubber(clean_node[k]) for k in target_keys if k in clean_node
            }

            # Sibling exploration
            # Recursively scrubs remaining sibling keys excluding the target keys.
            scrubbed_node = {
                k: _scrubber(v) for k, v in clean_node.items() if k not in target_keys
            }

            # Global aggregation path (consolidation engine)
            # Consolidates targets globally across nested sub-nodes if the global_merge feature is active.
            if features.get("global_merge", False):
                for sk, sv in scrubbed_node.items():
                    if isinstance(sv, dict):
                        found_targets.update(
                            {
                                mk: mv
                                for mk, mv in cast(dict[str, Any], sv).items()
                                if mk in target_keys
                            }
                        )
                    elif sk in target_keys:
                        found_targets[sk] = sv

                if found_targets:
                    return resolve_targets_func(found_targets)

            if found_targets:
                return resolve_targets_func(found_targets)

            # Upward consolidation / flattening engine
            # Flattens nested dictionaries upwards into a unified dictionary structure when global merge is enabled.
            if features.get("global_merge", False) and scrubbed_node:
                merged = {}
                for sk, sv in scrubbed_node.items():
                    if isinstance(sv, dict):
                        for mk, mv in cast(dict[str, Any], sv).items():
                            if not target_keys or mk in target_keys:
                                merged[mk] = mv
                    elif not target_keys or sk in target_keys:
                        merged[sk] = sv

                if merged:
                    return resolve_targets_func(merged)

            return scrubbed_node

        # PRIMITIVE PASS-THROUGH
        # Returns primitive node values directly without modification.
        return node

    return _scrubber
