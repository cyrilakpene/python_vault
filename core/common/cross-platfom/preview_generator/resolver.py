from typing import Any

from .formatter import format_seconds  # type: ignore[import-not-found]
from .calculator import calculate_midpoint_start, calculate_dynamic_end  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: PREVIEW SCHEMA RESOLUTION
# This utility dynamically resolves configuration schemas for media preview windows,
# generating default start or end time specifications based on runtime and prior resolution state.
# [>] EXECUTING PREVIEW SCHEMA RESOLUTION
def resolve_preview_schema(
    runtime_seconds: int, resolved_start: int | None = None
) -> dict[str, Any]:
    """
    Resolves configuration schemas for preview windows, providing default start or end times.

    Args:
        runtime_seconds (int): The total media runtime duration in seconds.
        resolved_start (int | None): The previously resolved start time in seconds, if any.

    Returns:
        dict[str, Any]: A schema dictionary defining the configuration key, label, cast type, and default value.
    """
    # START TIME SCHEMA RESOLUTION
    # If no start time has been resolved yet, calculates a midpoint heuristic start point
    # and returns a schema configuration requesting the start time input.
    if resolved_start is None:
        suggested_start: int = calculate_midpoint_start(runtime_seconds)
        readable_start: str = format_seconds(suggested_start)

        return {
            "key": "start_time",
            "label": f"Enter Start Time (Default: {readable_start})",
            "cast": "timestamp",
            "default": suggested_start,
        }

    # END TIME SCHEMA RESOLUTION
    # If a start time is already provided, calculates the corresponding dynamic end boundary
    # and returns a schema configuration requesting the end time input.
    suggested_end: int = calculate_dynamic_end(resolved_start, runtime_seconds)
    readable_end: str = format_seconds(suggested_end)

    return {
        "key": "end_time",
        "label": f"Enter End Time (Default: {readable_end})",
        "cast": "timestamp",
        "default": suggested_end,
    }
