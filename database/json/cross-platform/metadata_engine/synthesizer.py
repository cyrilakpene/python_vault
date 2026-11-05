from typing import Any, Literal, overload

from .validators import (
    validate_configuration,  # type: ignore[import-not-found]
    verify_source_signatures,  # type: ignore[import-not-found]
    check_target_overlap,  # type: ignore[import-not-found]
)
from .extractor import extract_source_value  # type: ignore[import-not-found]
from .builder import commit_value_to_tree, scrub_empty_branches  # type: ignore[import-not-found]
from .resolver import resolve_query_paths  # type: ignore[import-not-found]
from .formatter import apply_unit_formatting  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: METADATA SYNTHESIS & SIGNATURE-BASED JOIN PIPELINE
# This module provides overloaded typing signatures and a core orchestration function
# for synthesizing unified metadata trees from disparate raw sources with validation,
# virtual path resolution, extraction, unit formatting, and null-stripping support.
# [>] DEFINING OVERLOADED SIGNATURES & METADATA JOIN ENGINE
@overload
def join_metadata_by_signature(
    sources: dict[str, Any],
    signatures: dict[str, str],
    mapping_registry: dict[str, str],
    strip_null: Literal[True],
    scope: str | list[str],
    unit_configs: list[dict[str, list[str] | str]] | None = None,
    allow_target_overlap: bool = False,
) -> dict[str, Any]: ...


@overload
def join_metadata_by_signature(
    sources: dict[str, Any],
    signatures: dict[str, str],
    mapping_registry: dict[str, str],
    strip_null: Literal[False] = False,
    scope: str | list[str] | None = None,
    unit_configs: list[dict[str, list[str] | str]] | None = None,
    allow_target_overlap: bool = False,
) -> dict[str, Any]: ...


def join_metadata_by_signature(
    sources: dict[str, Any],
    signatures: dict[str, str],
    mapping_registry: dict[str, str],
    strip_null: bool = False,
    scope: str | list[str] | None = None,
    unit_configs: list[dict[str, list[str] | str]] | None = None,
    allow_target_overlap: bool = False,
) -> dict[str, Any]:
    """
    Synthesizes a unified metadata tree from disparate raw sources by coordinating
    validation, virtual path resolution, extraction, unit formatting, and tree building sub-modules.

    Args:
        sources (dict[str, Any]): A dictionary mapping source aliases to raw data pools.
        signatures (dict[str, str]): A dictionary mapping source aliases to mandatory signature keys.
        mapping_registry (dict[str, str]): A mapping registry linking source paths to destination target paths.
        strip_null (bool, optional): Flag indicating whether null or empty values within scope should be stripped.
          Defaults to False.
        scope (str | list[str] | None, optional): Target scopes or paths defining the null-stripping safe zone.
          Defaults to None.
        unit_configs (list[dict[str, list[str] | str]] | None, optional): A list of dicts defining units for specific leaf keys.
          Defaults to None.
        allow_target_overlap (bool, optional): Flag allowing multiple source paths to map to the same target leaf.
          Defaults to False.

    Returns:
        dict[str, Any]: The synthesized, unit-formatted, and pruned unified metadata tree.
    """
    # VIRTUAL PATH RESOLUTION & REGISTRY SANITIZATION
    # Intercepts dynamic bracketed queries (e.g., [id=123]) and resolves them into virtual pointers
    # before running validation and synthesis loops.
    if any("[" in k for k in mapping_registry.keys()):
        sources, mapping_registry = resolve_query_paths(sources, mapping_registry)

    # CONFIGURATION VALIDATION & SOURCE VERIFICATION
    # Validates configuration parameters (such as safe zone scopes for null stripping)
    # and verifies that all expected data sources contain mandatory signature keys[cite: 5].
    validate_configuration(strip_null, scope)
    verify_source_signatures(sources, signatures)

    # TARGET SCOPE INITIALIZATION & MAPPING PREPARATION
    # Normalizes scopes into a list, initializes tracking sets for assigned targets,
    # and prepares the final metadata dictionary container[cite: 5].
    target_scopes: list[str] = [scope] if isinstance(scope, str) else (scope or [])
    assigned_targets: set[str] = set()
    final_dict: dict[str, Any] = {}

    # MAPPING ITERATION & VALUE EXTRACTION
    # Iterates through each source-to-target mapping in the registry, extracting values,
    # evaluating null-stripping constraints within scope, applying unit formatting,
    # and guarding against target overlaps[cite: 5].
    for source_path, target_path in mapping_registry.items():
        # Extract value via extractor module
        current_val = extract_source_value(sources, source_path)

        # Handle null-stripping logic
        if strip_null:
            in_scope: bool = any(
                (s == ".") or (target_path == s) or (target_path.startswith(f"{s}."))
                for s in target_scopes
            )
            if in_scope and (current_val is None or current_val == ""):
                continue

        # Check target overlapping collisions
        check_target_overlap(target_path, assigned_targets, allow_target_overlap)

        # Apply unit conventions based on leaf key name and unit configurations
        leaf_key: str = target_path.split(".")[-1]
        value_to_commit = apply_unit_formatting(leaf_key, current_val, unit_configs)

        # Commit to tree via builder module (supporting advanced lists and padding)
        commit_value_to_tree(final_dict, target_path, value_to_commit)

    # BRANCH PRUNING & STATUS REPORTING
    # Scrubs empty skeleton branches and list elements from the tree, reports successful synthesis completion,
    # and returns the finalized metadata dictionary.
    result = scrub_empty_branches(final_dict)

    report_status(
        state="info",
        message="Synthesis complete: Metadata state consolidated successfully.",
        context=LogContext(
            component="database.join_metadata_by_signature",
            log_path=log_path,
            silent=False,
            trace_id="join_metadata_by_signature",
            actor=context.get("user"),
            payload={"target_scopes": target_scopes},
        ),
    )
    return result
