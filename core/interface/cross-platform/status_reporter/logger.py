import os
import json
from typing import Any, Callable
from datetime import datetime

from .constants import LogFormat, SEVERITY_LEVELS, SEVERITY_MAP  # type: ignore[import-not-found]


# LOG FORMATTING SUBSYSTEM: LEGACY LOG FORMATTER
# This utility maps legacy log parameters to their respective formatting callables,
# facilitating extensible O(1) format routing and legacy log string construction.
# [>] EXECUTING LEGACY LOG FORMATTING
def _legacy_formatter(
    ts: str,
    log_symbol: str,
    message: str,
    include_timestamp: bool,
    **kwargs: Any,
) -> str:
    """
    Formats a legacy log entry using a typed callable signature and optional keyword parameters.

    Args:
        ts (str): The timestamp string for the log entry.
        log_symbol (str): The symbol or severity indicator representing the log level.
        message (str): The primary log message text.
        include_timestamp (bool): A flag indicating whether to include the timestamp in the formatted output.
        **kwargs (Any): Additional flexible keyword arguments for extended formatting compatibility.

    Returns:
        str: The fully formatted legacy log entry string.
    """
    # LEGACY LOG FORMAT ROUTING
    # Delegates formatting to the core legacy log builder using the provided parameters.
    return _format_legacy_log(ts, log_symbol, message, include_timestamp)


# LOG FORMATTING SUBSYSTEM: STRUCTURED LOG FORMATTER
# This utility processes typed log parameters, diagnostic identifiers, performance metrics,
# and structured payloads to format comprehensive, machine-parsable JSON or structured log entries.
# [>] EXECUTING STRUCTURED LOG FORMATTING
def _structured_formatter(
    _ts: str,
    _log_symbol: str,
    message: str,
    _include_timestamp: bool,
    severity: str,
    component: str,
    trace_id: str | None = None,
    span_id: str | None = None,
    actor: str | None = None,
    elapsed_ms: float | int | None = None,
    steped: int | None = None,
    exception: str | None = None,
    payload: dict[str, Any] | None = None,
    **kwargs: Any,
) -> str:
    """
    Formats a structured log entry incorporating severity, component origin, tracing metadata, and payload data.

    Args:
        _ts (str): The timestamp string (ignored or handled by underlying structured formatter).
        _log_symbol (str): The symbol or severity indicator (subsumed by explicit severity parameter).
        message (str): The primary log message text describing the event.
        _include_timestamp (bool): Flag indicating whether timestamp inclusion is requested.
        severity (str): The severity level of the log entry (e.g., INFO, ERROR, DEBUG).
        component (str): The architectural component or module emitting the log.
        trace_id (str | None): Optional distributed tracing identifier for request correlation.
        span_id (str | None): Optional tracing span identifier for execution scope.
        actor (str | None): Optional identifier of the user or system entity triggering the action.
        elapsed_ms (float | int | None): Optional execution time elapsed in milliseconds.
        steped (int | None): Optional discrete step counter for modulo-based frequency throttling.
        exception (str | None): Optional serialized exception traceback or error summary.
        payload (dict[str, Any] | None): Optional dictionary containing structured contextual data.
        **kwargs (Any): Additional flexible keyword arguments for extended format compatibility.

    Returns:
        str: The fully formatted structured log entry string.
    """
    # STRUCTURED LOG FORMAT ROUTING
    # Delegates formatting to the core structured log builder using the provided metadata and telemetry parameters.
    return _format_structured_log(
        severity=severity,
        component=component,
        message=message,
        trace_id=trace_id,
        span_id=span_id,
        actor=actor,
        elapsed_ms=elapsed_ms,
        steped=steped,
        exception=exception,
        payload=payload,
    )


LOG_FORMATTER_MAP: dict[str, Callable[..., str]] = {
    "legacy": _legacy_formatter,
    "structured": _structured_formatter,
}


# LOGGING SUBSYSTEM: LEGACY LOG FORMATTING
# This utility builds classic human-readable plain text log lines incorporating timestamps,
# log symbols, and formatted message strings.
# [>] EXECUTING LEGACY LOG FORMATTING
def _format_legacy_log(
    ts: str, log_symbol: str, message: str, include_timestamp: bool
) -> str:
    """
    Builds the classic human-readable plain text log line.

    Args:
        ts (str): The timestamp string marking the log event.
        log_symbol (str): The symbol or status indicator representing the log severity.
        message (str): The detailed log message text.

    Returns:
        str: A formatted plain text log string terminated with a newline character.
    """
    # MESSAGE VALIDATION
    # Safely converts message to string, treating None as an empty string.
    safe_message = str(message or "")

    # LEGACY LOG LINE CONSTRUCTION
    # Formats and returns the timestamp, symbol, and message into a standardized plain text log line.
    if include_timestamp:
        if log_symbol:
            return f"[{ts}] {log_symbol} {safe_message}\n"
        return f"[{ts}] {safe_message}\n"

    if log_symbol:
        return f"{log_symbol} {safe_message}\n"

    return f"{safe_message}\n"


# LOGGING SUBSYSTEM: STRUCTURED JSON LOG RECORD BUILDER
# This utility constructs enterprise-grade structured JSON log records (JSONL) incorporating timestamps,
# severities, components, messages, trace IDs, span IDs, actors, elapsed durations, exceptions, and optional payload dictionaries.
# [>] EXECUTING STRUCTURED LOG FORMATTING
def _format_structured_log(
    severity: str,
    component: str,
    message: str,
    trace_id: str | None = None,
    span_id: str | None = None,
    actor: str | None = None,
    elapsed_ms: float | int | None = None,
    steped: int | None = None,
    exception: str | None = None,
    payload: dict[str, Any] | None = None,
) -> str:
    """
    Builds an enterprise-grade structured JSON log record (JSONL).

    Args:
        severity (str): The severity level of the log record (e.g., info, warn, fail).
        component (str): The subsystem or component emitting the log record.
        message (str): The detailed log message text.
        trace_id (str | None): Optional tracing identifier for request correlation. Defaults to None.
        span_id (str | None): Optional span identifier for sub-operation tracking. Defaults to None.
        actor (str | None): Optional actor or user identifier associated with the event. Defaults to None.
        elapsed_ms (float | int | None): Optional execution time elapsed in milliseconds. Defaults to None.
        exception (str | None): Optional exception message or error description string. Defaults to None.
        payload (dict[str, Any] | None): Optional supplementary contextual payload data. Defaults to None.

    Returns:
        str: A serialized JSONL formatted log string terminated with a newline character.
    """
    # BASE LOG ENTRY INITIALIZATION
    # Constructs the root log entry dictionary with ISO 8601 UTC timestamp, severity, component, and message.
    log_entry: dict[str, Any] = {
        "timestamp": datetime.now().isoformat() + "Z",
        "severity": severity,
        "component": component,
        "message": message,
    }

    # TRACE ID INCLUSION
    # Conditionally appends the trace identifier if provided for distributed tracking.
    if trace_id:
        log_entry["trace_id"] = trace_id

    # SPAN ID INCLUSION
    # Conditionally appends the span identifier if provided for sub-operation tracking.
    if span_id:
        log_entry["span_id"] = span_id

    # ACTOR METADATA INCLUSION
    # Conditionally appends the actor identifier if provided for auditing purposes.
    if actor:
        log_entry["actor"] = actor

    # ELAPSED DURATION INCLUSION
    # Conditionally appends performance execution time if provided.
    if elapsed_ms is not None:
        log_entry["elapsed_ms"] = elapsed_ms

    # ELAPSED DURATION INCLUSION
    # Conditionally appends performance execution steps if provided.
    if steped is not None:
        log_entry["steped"] = steped

    # EXCEPTION METADATA INCLUSION
    # Conditionally appends error or exception details if provided.
    if exception:
        log_entry["exception"] = exception

    # PAYLOAD DICTIONARY INCLUSION
    # Conditionally appends supplementary contextual payloads if provided.
    if payload:
        log_entry["payload"] = payload

    # JSON SERIALIZATION & LINE TERMINATION
    # Serializes the log entry dictionary into a compact JSON string and appends a newline character.
    return json.dumps(log_entry) + "\n"


# LOGGING SUBSYSTEM: BACKGROUND SESSION LOG COMMIT & SEVERITY GATE
# This utility manages background session logging by enforcing severity threshold gates,
# mapping status symbols to enterprise severity levels, handling trace contexts, and writing dual-mode formats safely.
# [>] EXECUTING LOG COMMIT
def commit_log(
    log_path: str | None,
    log_symbol: str,
    message: str,
    component: str,
    log_format: LogFormat,
    payload: dict[str, Any] | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    actor: str | None = None,
    elapsed_ms: float | int | None = None,
    steped: int | None = None,
    exception: str | None = None,
    min_severity: str = "INFO",
    include_timestamp: bool = True,
) -> None:
    """
    Manages background session logging, enforcing severity threshold gates,
    trace context handling, and dual-mode formatting with defensive error handling.

    Args:
        log_path (str | None): Optional file system path string where log entries are written.
        log_symbol (str): Symbol or prefix character identifying the log category or status.
        message (str): The content string to record in the log file.
        component (str): Module or application subsystem name emitting the log.
        log_format (LogFormat): Output format mode ("structured" or "legacy").
        payload (dict[str, Any] | None): Optional dictionary containing rich key-value telemetry data. Defaults to None.
        trace_id (str | None): Optional session or transaction trace identifier. Defaults to None.
        span_id (str | None): Optional span identifier for sub-operation tracking. Defaults to None.
        actor (str | None): Optional user or process identity string. Defaults to None.
        elapsed_ms (float | int | None): Optional execution time elapsed in milliseconds. Defaults to None.
        exception (str | None): Optional exception message or error description string. Defaults to None.
        min_severity (str): Minimum threshold level required to commit a log record. Defaults to "INFO".
        include_timestamp (bool): If True, passes real-time timestamp to the logger. Default to True.

    Returns:
        None: This function executes side effects by writing logs and does not return a value.
    """
    # LOG PATH EXISTENCE CHECK
    # Verifies that a valid log path target is provided before attempting file I/O operations.
    if log_path:
        try:
            # DIRECTORY AUTO-CREATION GUARD
            # Ensures parent directories exist prior to opening the target log file to prevent FileNotFoundError.
            log_dir = os.path.dirname(os.path.abspath(log_path))
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            # SYMBOL CLEANING & SEVERITY RESOLUTION
            # Cleans the log symbol and resolves it to a standardized enterprise severity level via the central map.
            clean_symbol = log_symbol.strip("[] ").strip()
            severity: str = SEVERITY_MAP.get(clean_symbol, "INFO")

            # SEVERITY THRESHOLD GATE CHECK
            # Evaluates current severity rank against the minimum threshold rank; bypasses logging if below threshold.
            current_rank = SEVERITY_LEVELS.get(severity, 20)
            threshold_rank = SEVERITY_LEVELS.get(min_severity.upper(), 20)
            if current_rank < threshold_rank:
                return

            # LOG STRING CONSTRUCTION VIA DICTIONARY LOOKUP
            # Generates the current timestamp and resolves the appropriate formatting function from the dispatcher map.
            ts = datetime.now().strftime("%H:%M:%S")
            formatter = LOG_FORMATTER_MAP.get(
                log_format, LOG_FORMATTER_MAP["structured"]
            )
            log_line = formatter(
                ts=ts,
                log_symbol=log_symbol,
                message=message,
                include_timestamp=include_timestamp,
                severity=severity,
                component=component or "core",
                trace_id=trace_id,
                span_id=span_id,
                actor=actor,
                elapsed_ms=elapsed_ms,
                steped=steped,
                exception=exception,
                payload=payload,
            )

            # SAFE FILE APPEND WITH UTF-8 ENCODING
            # Opens the log file in append mode and writes the formatted log entry securely.
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_line)

        except Exception:
            # DEFENSIVE EXCEPTION CATCH & SILENT FALLBACK
            # Catches unexpected file I/O or serialization exceptions to prevent logging failures from crashing the main execution flow.
            pass
