from typing import Any, Unpack, cast

from .heuristics import get_heuristics  # type: ignore[import-not-found]
from .resolver import resolve_source_data  # type: ignore[import-not-found]
from .scrubber import create_scrubber  # type: ignore[import-not-found]
from .model import FilterFeatures  # type: ignore[import-not-found]
from .contants import report_status, log_path  # type: ignore[import-not-found]


# DATA CONTAINER SUBSYSTEM: DATA DISTILLATION & MULTI-PASS FILTERING PIPELINE
# This utility coordinates raw data fetching, heuristic resolution, recursive scrubbing,
# and output stabilization to distill complex data structures based on patterns and feature flags.
# [>] EXECUTING DATA DISTILLATION & FILTERING PIPELINE
def fetch_filtered(
    path: str,
    source: dict[str, Any],
    patterns: list[str],
    target_keys: list[str],
    **features: Unpack[FilterFeatures],
) -> Any:
    """
    Fetches raw data and executes a multi-pass recursive scrub/flatten cycle.

    Args:
        path (str): The logical address path to fetch data from.
        source (dict[str, Any]): The source data container or dictionary pool.
        patterns (list[str]): Key prefix patterns to exclude during scrubbing.
        target_keys (list[str]): Specific keys targeted for hoisting and aggregation.
        **features (Unpack[FilterFeatures]): Keyword feature flags controlling strictness, merges, and flattening.

    Returns:
        Any: The distilled, scrubbed, and stabilized output payload.
    """
    # DISTILLATION TASK INITIALIZATION
    # Reports the start of the data distillation task for the specified target path.
    report_status(
        state="task",
        message=f"Initiating data distillation: Path {path!r}.",
        silent=True,
        log_path=log_path,
    )

    # HEURISTICS & STRATEGY ENGAGEMENT
    # Converts feature kwargs into a dictionary, instantiates corresponding heuristics,
    # and logs active global merge settings.
    feature_map = dict(features)
    heuristics = get_heuristics(path, feature_map)
    report_status(
        state="item",
        message=f"Heuristics engaged: Global Merge={feature_map.get('global_merge', False)}.",
        log_path=log_path,
        silent=True,
    )

    # SOURCE RESOLUTION & RECURSIVE SCRUBBING
    # Resolves raw data from the source via duck-typed routing, instantiates the recursive scrubber closure,
    # and executes the filtering pass over the payload.
    raw_data = resolve_source_data(path, source, feature_map)
    scrubber = create_scrubber(
        patterns,
        target_keys,
        cast(FilterFeatures, feature_map),
        heuristics["resolve_targets"],
    )
    filtered_output = scrubber(raw_data)

    # OUTPUT STABILIZATION & RETURN
    # Normalizes and stabilizes the scrubbed output according to strictness heuristics before returning.
    return heuristics["stabilize_output"](filtered_output)
