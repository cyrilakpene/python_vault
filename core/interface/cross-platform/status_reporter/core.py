from typing import Any

from .throttle import evaluate_throttle, cleanup_cache  # type: ignore[import-not-found]
from .logger import commit_log  # type: ignore[import-not-found]
from .stream import resolve_symbols, render_output  # type: ignore[import-not-found]
from .models import LogContext  # type: ignore[import-not-found]
from .constants import StatusState  # type: ignore[import-not-found]


# STATUS REPORTING & DIAGNOSTIC ORCHESTRATION ENGINE
# This utility coordinates high-visibility terminal feedback by orchestrating state mapping,
# frequency throttling, session logging, smart stream routing, and runtime cache hygiene.
# [>] EXECUTING STATUS REPORTING & ORCHESTRATION
def report_status(
    state: StatusState,
    message: str,
    context: LogContext | None = None,
    **kwargs: Any,
) -> None:
    """
    Renders high-visibility terminal feedback based on a symbolic state map,
    coordinating state mapping, throttling, persistence, stream routing, and cache cleanup.

    Args:
        state: The execution state or status classification string (e.g., 'info', 'warn', 'fail', 'done').
        message: The descriptive status message payload to log and render.
        context: Optional LogContext instance encapsulating configuration, telemetry, and tracing attributes.
        **kwargs: Additional arbitrary key-value telemetry attributes to merge into the log payload.
    """
    # CONTEXT INITIALIZATION
    # Instantiates a default LogContext if none is provided.
    if context is None:
        context = LogContext(component="core")

    # PAYLOAD MERGE & RESOLUTION
    # Combines context-level payload attributes with any additional runtime keyword arguments.
    payload = {**context.payload, **kwargs} if kwargs else context.payload

    # THROTTLING GATE CHECK
    # Evaluates step-based or temporal throttling intervals to filter recurring events,
    # ensuring terminal states always bypass limits.
    if not evaluate_throttle(state, message, context.is_loop, context.step):
        return

    # SYMBOLIC STATE RESOLUTION
    # Normalizes execution state strings and resolves appropriate UI display symbols
    # and log representation icons.
    normalized_state, display_symbol, log_symbol = resolve_symbols(state)

    # FILESYSTEM PERSISTENCE
    # Commits formatted log entries (structured or legacy) with metadata payload, trace context, and severity gates.
    commit_log(
        log_path=context.log_path,
        log_symbol=log_symbol,
        message=message,
        component=context.component,
        log_format=context.log_format,
        payload=payload if payload else None,
        trace_id=context.trace_id,
        span_id=context.span_id,
        actor=context.actor,
        elapsed_ms=context.elapsed_ms,
        exception=context.exception,
        min_severity=context.min_severity,
        include_timestamp=context.include_timestamp,
    )

    # STREAM ROUTING, VERBOSITY, & TERMINAL RENDERING
    # Evaluates verbosity gates, silence gates, and smart stream routing before printing
    # the formatted message to the active terminal stream.
    render_output(
        message=message,
        display_symbol=display_symbol,
        normalized_state=normalized_state,
        stream=context.stream,
        is_verbose=context.is_verbose,
        silent=context.silent,
    )

    # CACHE CLEANUP FOR TERMINAL STATES
    # Purges completed or failed terminal state messages from the global loop cache
    # to prevent memory leaks during long execution runs.
    cleanup_cache(state, message)
