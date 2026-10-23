from typing import TextIO, Literal, TypeAlias

from .throttle import evaluate_throttle, cleanup_cache  # type: ignore[import-not-found]
from .logger import commit_log  # type: ignore[import-not-found]
from .stream import resolve_symbols, render_output  # type: ignore[import-not-found]

# TYPE DEFINITION: SYMBOLIC STATE MAPPING
# Defines the exhaustive set of valid status keys. Using a TypeAlias
# ensures static analysis tools can validate state transitions at
# development time, reducing runtime errors caused by typos.
StatusState: TypeAlias = Literal[
    "task",
    "info",
    "log_info",
    "warn",
    "item",
    "done",
    "fail",
    "input",
    "debug",
    "proc",
]


# STATUS REPORTING & DIAGNOSTIC ORCHESTRATION ENGINE
# This utility coordinates high-visibility terminal feedback by orchestrating state mapping,
# frequency throttling, session logging, smart stream routing, and runtime cache hygiene.
# [>] EXECUTING STATUS REPORTING & ORCHESTRATION
def report_status(
    state: StatusState,
    message: str,
    stream: TextIO | None = None,
    log_path: str | None = None,
    is_verbose: bool = False,
    silent: bool = False,
    is_loop: float | int | bool = False,
    step: int | None = None,
) -> None:
    """
    Renders high-visibility terminal feedback based on a symbolic state map,
    coordinating state mapping, throttling, persistence, stream routing, and cache cleanup.

    Args:
        state: The execution state or status classification string (e.g., 'info', 'warn', 'fail', 'done').
        message: The descriptive status message payload to log and render.
        stream: Optional custom text stream output target (defaults to stdout/stderr).
        log_path: Optional file path string for background session log persistence.
        is_verbose: Boolean flag enabling verbose debug message output.
        silent: Boolean flag suppressing normal non-verbose console outputs.
        is_loop: Throttling control threshold (boolean, modulo interval integer, or time-delta float).
        step: Optional discrete step counter for modulo-based frequency throttling.
    """
    # THROTTLING GATE CHECK
    # Evaluates step-based or temporal throttling intervals to filter recurring events,
    # ensuring terminal states bypass limits.
    if not evaluate_throttle(state, message, is_loop, step):
        return

    # SYMBOLIC STATE RESOLUTION
    # Normalizes execution state strings and resolves appropriate UI display symbols
    # and log representation icons.
    normalized_state, display_symbol, log_symbol = resolve_symbols(state)

    # FILESYSTEM PERSISTENCE
    # Commits formatted log entries with timestamps to the specified background log path.
    commit_log(log_path, log_symbol, message)

    # STREAM ROUTING, VERBOSITY, & TERMINAL RENDERING
    # Evaluates verbosity gates, silence flags, and smart stream routing before printing
    # the formatted message to the active terminal stream.
    render_output(message, display_symbol, normalized_state, stream, is_verbose, silent)

    # CACHE CLEANUP FOR TERMINAL STATES
    # Purges completed or failed terminal state messages from the global loop cache
    # to prevent memory leaks during long execution runs.
    cleanup_cache(state, message)
