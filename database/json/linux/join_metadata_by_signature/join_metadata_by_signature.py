import sys
import copy
from typing import Any, Literal, overload


# ARCHITECTURAL GATEKEEPER: RECURSIVE METADATA SYNTHESIS ENGINE
# This engine serves as the "State of Truth" synthesizer. It performs deep-path
# extraction from disparate raw sources and constructs a unified, collision-guarded
# tree. The architecture is designed to prevent "Schema Drift" and "Ghost Mutations"
# by enforcing strict isolation between raw inputs and synthesized outputs.
@overload
def join_metadata_by_signature(
    sources: dict[str, Any],
    signatures: dict[str, str],
    mapping_registry: dict[str, str],
    strip_null: Literal[True],
    scope: str | list[str],
    allow_target_overlap: bool = False,
) -> dict[str, Any]: ...


@overload
def join_metadata_by_signature(
    sources: dict[str, Any],
    signatures: dict[str, str],
    mapping_registry: dict[str, str],
    strip_null: Literal[False] = False,
    scope: str | list[str] | None = None,
    allow_target_overlap: bool = False,
) -> dict[str, Any]: ...


def join_metadata_by_signature(
    sources: dict[str, Any],
    signatures: dict[str, str],
    mapping_registry: dict[str, str],
    strip_null: bool = False,
    scope: str | list[str] | None = None,
    allow_target_overlap: bool = False,
) -> dict[str, Any]:
    """
    Synthesizes a unified metadata tree from disparate raw sources.
    Performs deep-path extraction, data isolation, and collision-guarded construction.
    """

    # CONFIGURATION INTEGRITY CHECK
    # We prevent "Silent Data Loss." If stripping is enabled without a scope,
    # the engine might prune nodes the user intended to keep. We force an explicit
    # declaration of the "Safe Zone" for pruning.
    if strip_null and scope is None:
        raise ValueError(
            f"[!] CONFIGURATION ERROR: 'scope' must be defined when 'strip_null' is True. "
            f"Pass a string or a list of strings (e.g., ['general', '.'])."
        )

    # SCOPE NORMALIZATION
    # Ensures the traversal logic can iterate over a list regardless of
    # whether the user provided a single string or a collection.
    target_scopes: list[str] = [scope] if isinstance(scope, str) else (scope or [])

    # OVERLAP TRACKING: DESTINATION GUARDIAN
    # In a Source -> Target mapping, multiple sources could point to the same
    # destination. This set tracks "Claimed Real Estate" in the final tree to
    # prevent accidental overwrites unless the user explicitly allows overlap.
    assigned_targets: set[str] = set()

    # SOURCE INTEGRITY VERIFICATION: IDENTITY CHECK
    # If a source (like FFprobe) failed or returned an empty object, we must
    # halt before processing junk data. The "Identity Key" (Signature) acts as
    # a proof-of-life for the raw data source.
    for alias, sig_key in signatures.items():
        source_content: dict[str, Any] = sources.get(alias, {})
        if sig_key not in source_content:
            raise KeyError(
                f"[!] INTEGRITY FAILURE: Source '{alias}' is missing "
                f"the mandatory signature key: '{sig_key}'. This prevents "
                f"synthesizing data from corrupted or missing inputs."
            )

    # TARGET REGISTRY INITIALIZATION
    final_dict: dict[str, Any] = {}

    # THE SYNTHESIS LOOP: PATH RECONCILIATION
    # This is the core transformation. We iterate through the registry to
    # map the "Wild" raw paths into our "Clean" architectural schema.
    for source_path, target_path in mapping_registry.items():
        current_val: Any = None

        # RECURSIVE SOURCE EXTRACTION: DOT-NOTATION RESOLUTION
        # Raw sources are often deeply nested. We resolve "key.subkey.0"
        # notation into actual values, supporting both Dictionary keys and
        # List indices to handle the complexity of JSON metadata structures.
        if isinstance(source_path, str) and "." in source_path:
            src_parts: list[str] = source_path.split(".")
            current_val = sources.get(src_parts[0], {})

            for part in src_parts[1:]:
                if isinstance(current_val, dict):
                    current_val = current_val.get(part)
                elif isinstance(current_val, list) and part.isdigit():
                    idx: int = int(part)
                    current_val = current_val[idx] if idx < len(current_val) else None
                else:
                    # Path resolution failed mid-traversal; treat as missing.
                    current_val = None
                    break
        else:
            # If no dot is present, we treat the source_path as a literal
            # value or a top-level key.
            current_val = source_path

        # MULTI-SURGICAL NULL-STRIPPING: SCOPE-BASED PRUNING
        # Clean schemas should not contain "noise." If a value is empty,
        # we check if it falls within a "Prune-able Scope." If it does, we
        # abort the commitment to keep the final tree lean and actionable.
        if strip_null:
            in_scope: bool = any(
                (s == ".") or (target_path == s) or (target_path.startswith(f"{s}."))
                for s in target_scopes
            )

            if in_scope and (current_val is None or current_val == ""):
                # [d] STRIPPING NULL VALUE: {target_path} is out of scope/empty.
                continue

        # TARGET OVERLAP GUARD: SCHEMATIC EXCLUSIVITY
        # Prevents "Mapping Collisions." If two different sources try to
        # fill the same slot (e.g. video.width), we raise an error to force
        # the developer to choose a single source of truth or enable overlap.
        if not allow_target_overlap and target_path in assigned_targets:
            raise ValueError(
                f"[!] TARGET COLLISION: Multiple source paths are attempting to "
                f"populate the same target leaf: '{target_path}'. Check registry."
            )
        assigned_targets.add(target_path)

        # DEEP-PATH ISOLATION: IMMUTABILITY ENFORCEMENT
        # We must decouple the synthesized tree from the raw sources.
        # Without deepcopy, modifying the final metadata would accidentally
        # mutate the original raw sources in memory (Shared Reference).
        value_to_commit = (
            copy.deepcopy(current_val)
            if isinstance(current_val, (dict, list))
            else current_val
        )

        # COLLISION-GUARDED TREE CONSTRUCTION: SCHEMA ENFORCEMENT
        # This prevents "Branch-Leaf Collisions." We ensure we don't
        # try to turn an existing value into a folder, or an existing
        # folder into a value, which would destroy the tree structure.
        target_parts: list[str] = target_path.split(".")
        cursor: dict[str, Any] = final_dict

        for node in target_parts[:-1]:
            if node in cursor and not isinstance(cursor[node], dict):
                raise TypeError(
                    f"[!] SCHEMA COLLISION: Path node '{node}' is already a "
                    f"Value and cannot be transformed into a Branch (Folder)."
                )
            cursor = cursor.setdefault(node, {})

        # FINAL VALUE COMMITMENT: LEAF PROMOTION
        # This is the terminal assignment. We verify the destination
        # isn't already a branch before committing the final value.
        last_key: str = target_parts[-1]

        if last_key in cursor and isinstance(cursor[last_key], dict):
            raise TypeError(
                f"[!] SCHEMA COLLISION: Terminal key '{last_key}' is already "
                f"defined as a Branch and cannot be overwritten by a Value."
            )

        cursor[last_key] = value_to_commit

    # POST-PROCESSING: GHOST BRANCH EXCISION
    # Null-stripping can leave behind empty "Skeleton" dictionaries
    # (e.g., {"video": {"codec": {}}}). This bottom-up recursion cleanses
    # the tree so only branches containing actual data remain.
    def _scrub_empty_branches(node: Any) -> Any:
        if not isinstance(node, dict):
            return node

        # Process children first to ensure we catch branches that become empty.
        cleaned_node: dict[str, Any] = {
            k: _scrub_empty_branches(v) for k, v in node.items()
        }

        return {
            k: v
            for k, v in cleaned_node.items()
            if not (isinstance(v, dict) and len(v) == 0)
        }

    # FINAL SYNTHESIZED SCHEMA EMISSION
    # [+] SYNTHESIS COMPLETE: METADATA STATE CONSOLIDATED
    return _scrub_empty_branches(final_dict)
