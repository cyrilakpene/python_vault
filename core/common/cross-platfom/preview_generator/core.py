from typing import Any

from .resolver import resolve_preview_schema  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: PREVIEW SCHEMA WRAPPER
# This utility wraps preview schema resolution, delegating to resolve_preview_schema
# for configuring media preview window inputs based on runtime and resolution state.
# [>] EXECUTING PREVIEW SCHEMA RETRIEVAL
def get_preview_schema(
    runtime_seconds: int, resolved_start: int | None = None
) -> dict[str, Any]:
    """
    Retrieves the preview schema configuration by delegating to the resolver utility.

    Args:
        runtime_seconds (int): The total media runtime duration in seconds.
        resolved_start (int | None): The previously resolved start time in seconds, if any.

    Returns:
        dict[str, Any]: A schema dictionary defining the configuration key, label, cast type, and default value.
    """
    # SCHEMA DELEGATION
    # Delegates schema resolution to resolve_preview_schema with the provided runtime and start time parameters.
    return resolve_preview_schema(runtime_seconds, resolved_start)
