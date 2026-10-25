from typing import Any, cast


# DATA CONTAINER SUBSYSTEM: SOURCE DATA RESOLUTION & DUCK-TYPED ROUTING
# This utility resolves logical addresses from either a pipeline orchestrator instance
# or a primitive dictionary, supporting recursive segment traversal and strict error handling.
# [>] EXECUTING SOURCE DATA RESOLUTION
def resolve_source_data(path: str, source: Any, features: dict[str, Any]) -> Any:
    """
    Resolves logical address from a Pipeline orchestrator or a primitive dictionary.

    Args:
        path (str): The dot-notated string path targeting the data source.
        source (Any): The source object (pipeline instance or raw dictionary) to query.
        features (dict[str, Any]): Feature flag configurations controlling strictness and traversal rules.

    Returns:
        Any: The resolved data node or container payload.
    """
    # DUCK-TYPED PIPELINE DETECTION
    # Checks whether the provided source object implements the pipeline query interface (`get_data`).
    is_pipeline = hasattr(source, "get_data") and callable(source.get_data)

    # PIPELINE ROUTING VS PRIMITIVE TRAVERSAL
    # If the source is a valid pipeline instance, delegate data retrieval directly via the path parameter.
    if is_pipeline:
        return source.get_data(path=path)
    else:
        # RAW DICTIONARY INITIALIZATION & SEGMENT TRAVERSAL
        # Fallback to dictionary traversal, iterating through dot-separated path segments
        # and respecting strict mode key error constraints if a segment is missing.
        raw_data: Any = source if source is not None else {}
        if path and isinstance(raw_data, dict):
            for segment in path.split("."):
                if isinstance(raw_data, dict) and segment in raw_data:
                    raw_data = cast(dict[str, Any], raw_data)[segment]
                elif features.get("strict", False):
                    raise KeyError(
                        f"Critical path failure: Segment {segment!r} not found in {path!r}."
                    )
                else:
                    raw_data = {}
                    break
        return cast(Any, raw_data)
