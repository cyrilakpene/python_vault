import sys
import time
from typing import TextIO
from datetime import datetime
from typing import Literal, TypeAlias

# PERSISTENCE LAYER: LOOP STATE CACHE
# This dictionary tracks the last-rendered timestamp for specific messages.
# By residing at the module level, it persists across multiple function calls
# within the same execution session, enabling time-based filtering.
_LOOP_CACHE: dict[str, float | int] = {}

# TYPE DEFINITION: SYMBOLIC STATE MAPPING
# Defines the exhaustive set of valid status keys. Using a TypeAlias
# ensures static analysis tools can validate state transitions at
# development time, reducing runtime errors caused by typos.
StatusState: TypeAlias = Literal[
    "task",
    "info",
    "log_info",
    "warn",
    "done",
    "fail",
    "input",
    "debug",
    "proc",
]


# SYMBOLIC STATUS REPORTING PIPELINE
# This module implements a character-based terminal feedback system. By
# utilizing a localized mapping of status indicators, we ensure that
# the application provides granular, parseable visual feedback without
# polluting the global namespace.
def report_status(
    state: str,
    message: str,
    stream: TextIO | None = None,
    log_path: str | None = None,
    is_verbose: bool = False,
    silent: bool = False,
    is_loop: float | int | bool = False,
    step: int | None = None,
) -> None:
    """Renders high-visibility terminal feedback based on a symbolic state map.

    Ensures consistent visual reporting and background session logging across the
    entire application lifecycle. Handles automatic output throttling for recurring
    events using time intervals or step milestones.

    Args:
        state: The symbolic key (e.g., 'done', 'fail', 'item') representing the event state.
        message: The descriptive text to be rendered alongside the status symbol.
        stream: Target IO stream for terminal output (defaults to stdout, or stderr for errors).
        log_path: File system path for background session logging.
        is_verbose: Toggle for high-density reporting; suppresses 'debug' calls if False.
        silent: Global override; if True, suppresses terminal output while honoring logs.
        is_loop: Throttle interval. Acts as seconds for time-based evaluation, or as
            the milestone step frequency when `step` is provided.
        step: Optional current execution index (e.g., chunk or row count). Enables
            modulo-based milestone throttling when paired with `is_loop`.
    """

    # THROTTLING GATE: TEMPORAL & STEP-BASED NOISE REDUCTION
    # Evaluates whether the current execution cycle warrants rendering based on
    # step frequency (modulo) or elapsed temporal duration. Terminal states
    # ('done', 'fail') always bypass this gate to guarantee execution finality.
    # [>] EVALUATING LOOP THROTTLE
    if is_loop:
        is_terminal_state = state.lower() in ["done", "fail"]

        # STEP-BASED THROTTLE: DISCRETE MILESTONE EVALUATION
        # If an explicit step index is supplied, we perform modulo math against
        # the requested interval. Always fires on step 0 to confirm initialization.
        if step is not None:
            interval = int(is_loop)
            is_due = (step == 0) or (step % interval == 0)

            if not is_due and not is_terminal_state:
                # MILESTONE EXIT: Current step index is not a designated interval.
                return

        # TEMPORAL THROTTLE: TIME-DELTA DURATION EVALUATION
        # Fallback mechanism when step is omitted. Evaluates time elapsed against
        # system clock since the previous execution cached for this message key.
        else:
            now_ts = time.time()
            last_ts = float(_LOOP_CACHE.get(message, 0.0))

            is_due = (now_ts - last_ts) >= float(is_loop)

            if not is_due and not is_terminal_state:
                # TIME-DELTA EXIT: Requested duration interval has not elapsed.
                return

            # Synchronize state cache with current execution timestamp
            _LOOP_CACHE[message] = now_ts

    # LOCALIZED SYMBOLIC MAPPING: ENCAPSULATED STATUS INDICATORS
    # We define the status indicators within the function scope to enforce
    # encapsulation. This ensures the 'Business Logic' of the reporter
    # remains self-contained and prevents unintended side-effects in
    # the broader application state.
    # [>] INITIALIZING STATUS MAP
    # Usage:
    #   'task' = start/direction, 'info' = context/flow, 'warn' = attention, 'item' = sub-details
    #   'done' = success, 'fail' = failure, 'input' = interaction, 'debug' = technical detail
    #   'proc' = active/processing
    status_map: dict[str, str] = {
        "task": "[>]",
        "info": "[~]",
        "log_info": " [~]",
        "warn": "[!]",
        "item": "  [-]",
        "done": "[+]",
        "fail": "[x]",
        "input": "[?]",
        "debug": " [d]",
        "proc": "[*]",
    }

    # SYMBOL VALIDATION: DEFENSIVE STATE RESOLUTION
    # We utilize a default character for undefined states to prevent
    # execution crashes. This provides a defensive layer when the
    # calling code passes an unrecognized status key.
    # [>] RESOLVING SYMBOLIC CHARACTER
    normalized_state = str(state or "").lower()

    display_key = "info" if normalized_state == "log_info" else normalized_state
    display_symbol: str = status_map.get(display_key, "[ ]")

    log_key = "log_info" if normalized_state == "info" else normalized_state
    log_symbol: str = status_map.get(log_key, display_symbol)

    # PERSISTENCE GATE: BACKGROUND SESSION LOGGING
    # If a log_path is provided, we commit the event to the filesystem.
    # We use 'append' mode to ensure multiple modules can contribute to
    # the same session log without overwriting previous entries.
    # [>] EXECUTING FILE SYSTEM COMMIT
    if log_path:
        try:
            # We open/close immediately to ensure the log is "Flushed" to disk.
            # This ensures that even if a crash occurs, the history is safe.
            # 'encoding="utf-8"' is enforced for cross-platform log consistency.
            with open(log_path, "a", encoding="utf-8") as f:
                # We inject a timestamp for the log file only to provide
                # chronological context without polluting the terminal UI.
                ts = datetime.now().strftime("%H:%M:%S")
                f.write(f"[{ts}] {log_symbol} {message}\n")
        except Exception:
            # DEFENSIVE EXIT: If the filesystem is read-only or full,
            # we fail silently to prevent interrupting the main UI flow.
            # This ensures the 'Terminal Output Pipeline' remains the priority.
            pass

    # VERBOSITY GATE: SIGNAL VS. NOISE
    # If the requested state is 'debug', we check the local verbosity flag.
    # This prevents terminal clutter by ensuring low-level diagnostics only
    # appear when explicitly requested by the operator.
    # [>] EVALUATING VERBOSITY STATE
    if normalized_state == "debug" and not is_verbose:
        # QUIET EXIT: The operator has not requested high-density reporting,
        # so we suppress this signal to maintain terminal clarity.
        return

    # THE SILENCE GATE (Responsibility: Operator Preference)
    # We handle 'silent' as a separate priority. Even if a message
    # passes (e.g., it's a 'task' or 'info'), this gate can
    # still suppress it based on the specific function call's intent.
    # [>] EVALUATING SILENCE PROTOCOL
    if silent and not is_verbose:
        # OPERATOR OVERRIDE: The silence flag is active and verbosity
        # is not high enough to bypass it. We terminate the report
        # immediately to ensure the terminal remains clean.
        return

    # LOGIC GATE: STREAM ROUTING & FALLBACK
    # If no specific stream is provided, we implement "Smart Routing."
    # Warning and Failure states are pivoted to 'sys.stderr' to ensure
    # critical visibility even when 'stdout' is redirected to a file.
    # [>] EXECUTING STREAM RESOLUTION
    if stream is None:
        # PIPELINE SEPARATION: We divert 'warn' and 'fail' to stderr.
        # This ensures that if the operator redirects output to a log
        # file (e.g., '> log.txt'), critical errors still appear in
        # the terminal for immediate intervention.
        stream = sys.stderr if normalized_state in ["warn", "fail"] else sys.stdout

    # TERMINAL OUTPUT PIPELINE: VISUAL STRING CONSTRUCTION
    # The final visual string is constructed using f-string interpolation
    # for high-performance string formatting. We use 'flush=True' to
    # guarantee that unbuffered streams (stderr) appear instantly.
    # [>] EXECUTING TERMINAL DRAW
    print(f"{display_symbol} {message}", file=stream, flush=True)

    # CACHE CLEANUP: MEMORY MANAGEMENT
    # If the process is finished, we remove the message from the cache
    # to prevent memory growth and allow future reuse of the message string.
    # [>] EXECUTING CACHE PURGE
    if normalized_state in ["done", "fail"] and message in _LOOP_CACHE:
        _LOOP_CACHE.pop(message, None)
