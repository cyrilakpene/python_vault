import re
from dataclasses import dataclass, field
from typing import Any, Callable


# TELEMETRY SUBSYSTEM: METRIC CONFIGURATION DATACLASS
# This utility defines the type-safe configuration rules and default values
# for individual regex metric extraction procedures.
# [>] EXECUTING METRIC CONFIG DATACLASS DEFINITION
@dataclass
class MetricConfig:
    """Configuration rules for an individual regex metric extraction."""

    # REGEX PATTERN DEFINITION
    # The string or compiled regex pattern used to scan telemetry data.
    regex: str | re.Pattern[str]

    # DEFAULT FALLBACK VALUE
    # The default value returned if the metric pattern is not matched.
    default: Any = None

    # STRICT VALIDATION FLAG
    # Flag indicating whether a missing match should trigger a strict error tracking key.
    strict: bool = False

    # TARGET CAPTURE GROUP
    # The capture group index or collection of indices to extract from regex matches.
    group: int | tuple[int, ...] | list[int] = 1


# TELEMETRY SUBSYSTEM: METRICS & CALCULATIONS SCHEMA DATACLASS
# This utility encapsulates schema configurations for regex metric extractions
# and derivative calculation formulas used during telemetry processing.
# [>] EXECUTING SCHEMA DATACLASS DEFINITION
@dataclass
class Schema:
    """Encapsulates regex metric configurations and derivative calculation formulas."""

    # METRICS CONFIGURATION MAPPING
    # Dictionary mapping metric names to their regex pattern strings, compiled patterns, or MetricConfig definitions.
    metrics: dict[str, str | re.Pattern[str] | MetricConfig] = field(
        default_factory=lambda: dict[str, str | re.Pattern[str] | MetricConfig]()
    )

    # CALCULATIONS FORMULA MAPPING
    # Dictionary mapping calculation targets to callables for deriving secondary metrics from extracted telemetry.
    calculations: dict[str, dict[str, Callable[[dict[str, Any]], Any]]] = field(
        default_factory=lambda: dict[str, dict[str, Callable[[dict[str, Any]], Any]]]()
    )


# PIPELINE SUBSYSTEM: SUBTYPE CONFIGURATION DATACLASS
# This utility defines the processing category and target execution context
# for routing and categorizing pipeline jobs and operations.
# [>] EXECUTING SUBTYPE DATACLASS DEFINITION
@dataclass
class SubType:
    """Defines the processing category and target execution context for the pipeline."""

    # PROCESSING CATEGORY
    # The primary category classification for pipeline processing operations.
    category: str = "global"

    # TARGET EXECUTION CONTEXT
    # The specific target execution environment or context for the operations.
    target_context: str = "global"


# TELEMETRY SUBSYSTEM: TELEMETRY METADATA DATACLASS
# This utility defines diagnostic execution metadata returned alongside the telemetry manifest
# during processing and verification runs.
# [>] EXECUTING TELEMETRY METADATA DATACLASS DEFINITION
@dataclass
class TelemetryMetadata:
    """Diagnostic execution metadata returned alongside the telemetry manifest."""

    # EXECUTION STATUS STRING
    # The overall status string indicating the result of the telemetry extraction process.
    status: str

    # MISSING STRICT METRICS LIST
    # List of strict metric keys that were missing from the log buffer during extraction.
    missing_strict: list[str]

    # SKIPPED CALCULATIONS LIST
    # List of derivative calculation formulas that were skipped due to unmet dependencies.
    skipped_calculations: list[str]

    # EXECUTION CONTEXT STRING
    # The target execution context string associated with the telemetry run.
    context: str
