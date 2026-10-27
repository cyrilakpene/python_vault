from typing import Any

from .source_resolver import resolve_data_source  # type: ignore[import-not-found]
from .extractor import extract_metrics  # type: ignore[import-not-found]
from .calculator import compute_calculations  # type: ignore[import-not-found]
from .models import Schema, SubType, TelemetryMetadata  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: INDUSTRIAL TELEMETRY GATHERING & PARSING
# This utility parses raw industrial log streams into structured telemetry objects using strongly typed schemas,
# supporting both modern dataclass structures and legacy dictionaries with robust normalization.
# [>] EXECUTING INDUSTRIAL TELEMETRY GATHERING
def gather_industrial_telemetry(
    data_input: str,
    schema: Schema | dict[str, Any],
    sub_type: SubType | tuple[str, str] = ("global", "global"),
    keep_nulls: bool = True,
    protected_keys: list[str] | None = None,
    return_all: bool = False,
) -> dict[str, Any]:
    """
    Parses raw log strings into structured telemetry objects using strongly typed schemas.

    Args:
        data_input (str): The log file path or raw stream buffer string to analyze.
        schema (Schema | dict[str, Any]): The parsing schema container or configuration dictionary.
        sub_type (SubType | tuple[str, str]): The processing sub-type object or legacy context tuple.
        keep_nulls (bool): Flag indicating whether to retain null values in the final manifest.
        protected_keys (list[str] | None): A list of architectural keys exempt from null purging.
        return_all (bool): Flag dictating whether to extract all matching metrics or only strict fields.

    Returns:
        dict[str, Any]: A structured dictionary containing the telemetry manifest and diagnostic metadata.
    """
    # INITIALIZE PROTECTED KEYS
    # Establishes an empty default list for protected keys if none are provided.
    protected_keys = protected_keys or []

    # SUB_TYPE NORMALIZATION
    # Resolves the target execution context from either a modern SubType dataclass or legacy tuple.
    if isinstance(sub_type, SubType):
        target_context = sub_type.target_context
    else:
        _, target_context = sub_type

    # SCHEMA CONFIGURATION NORMALIZATION
    # Extracts metrics and calculation configurations from either a Schema dataclass or legacy dictionary.
    if isinstance(schema, Schema):
        metrics_cfg = schema.metrics
        calc_cfg = schema.calculations
    else:
        metrics_cfg = schema.get("metrics", {})
        calc_cfg = schema.get("calculations", {})

    # DATA SOURCE RESOLUTION
    # Resolves the raw data input into a readable log string from a file path or stream buffer.
    log_text = resolve_data_source(data_input)

    # REGEX METRIC EXTRACTION
    # Processes the log text against metric extraction rules to yield the working manifest and missing strict keys.
    manifest, missing_strict_keys = extract_metrics(
        log_text=log_text,
        metrics_cfg=metrics_cfg,
        return_all=return_all,
    )

    # DERIVATIVE CALCULATION EVALUATION
    # Evaluates calculation formulas across the designated execution stack and tracks any skipped items.
    manifest, skipped_calcs = compute_calculations(
        manifest=manifest,
        calc_cfg=calc_cfg,
        target_context=target_context,
        missing_strict_keys=missing_strict_keys,
    )

    # MANIFEST REGISTRY PURIFICATION
    # Purges null values from the manifest registry if keep_nulls is disabled.
    if not keep_nulls:
        manifest = {k: v for k, v in manifest.items() if v is not None}

    # METADATA ENCAPSULATION
    # Constructs a strongly typed TelemetryMetadata object capturing execution status and context details.
    metadata = TelemetryMetadata(
        status="CRITICAL_MISSING" if missing_strict_keys else "SUCCESS",
        missing_strict=missing_strict_keys,
        skipped_calculations=skipped_calcs,
        context=target_context,
    )

    # OUTPUT DICTIONARY BINDING
    # Encapsulates the purified manifest and metadata attributes into the final structured output dictionary.
    return {
        "manifest": manifest,
        "metadata": {
            "status": metadata.status,
            "missing_strict": metadata.missing_strict,
            "skipped_calculations": metadata.skipped_calculations,
            "context": metadata.context,
        },
    }
