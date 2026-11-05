from dataclasses import dataclass, field
from typing import Any, TextIO

from .constants import LogFormat  # type: ignore[import-not-found]


# DATACLASS DEFINITION: LOGGING & TELEMETRY CONTEXT
# Encapsulates contextual metadata, formatting options, tracing parameters,
# and execution flags for structured log generation and status reporting.
@dataclass
class LogContext:
    """
    Encapsulates execution context, configuration options, and telemetry metadata
    for status reporting and structured session logging.

    Attributes:
        component (str): Module or application subsystem name emitting the log.
        log_format (LogFormat): Output format mode for session logs ("structured" or "legacy"). Defaults to "structured".
        stream (TextIO | None): Optional custom text stream output target (defaults to stdout/stderr). Defaults to None.
        log_path (str | None): Optional file path string for background session log persistence. Defaults to None.
        is_verbose (bool): Boolean flag enabling verbose debug message output. Defaults to False.
        silent (bool): Boolean flag suppressing normal non-verbose console outputs. Defaults to False.
        is_loop (float | int | bool): Throttling control threshold (boolean, modulo interval integer, or time-delta float). Defaults to False.
        step (int | None): Optional discrete step counter for modulo-based frequency throttling. Defaults to None.
        trace_id (str | None): Optional session or transaction trace identifier for distributed tracking. Defaults to None.
        span_id (str | None): Optional span identifier for sub-operation tracking. Defaults to None.
        actor (str | None): Optional user or process identity string for auditing. Defaults to None.
        min_severity (str): Minimum threshold level required to commit a log record. Defaults to "INFO".
        elapsed_ms (float | int | None): Optional execution time elapsed in milliseconds. Defaults to None.
        exception (str | None): Optional exception message or error description string. Defaults to None.
        include_timestamp (bool): If True, passes real-time timestamp to the logger. Default to True.
        payload (dict[str, Any]): Rich key-value telemetry payload attributes to record in structured log records.
    """

    component: str
    log_format: LogFormat = "structured"
    stream: TextIO | None = None
    log_path: str | None = None
    is_verbose: bool = False
    silent: bool = False
    is_loop: float | int | bool = False
    step: int | None = None
    trace_id: str | None = None
    span_id: str | None = None
    actor: str | None = None
    min_severity: str = "INFO"
    elapsed_ms: float | int | None = None
    exception: str | None = None
    include_timestamp: bool = True
    payload: dict[str, Any] = field(default_factory=dict[str, Any])
