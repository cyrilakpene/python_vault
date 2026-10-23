import time

from .cache import LOOP_CACHE  # type: ignore[import-not-found]


# THROTTLE EVALUATION & RECURRING EVENT FILTERING ENGINE
# This utility filters recurring log or status events based on discrete step intervals
# or temporal time-delta durations, ensuring terminal states always bypass throttling limits.
# [>] EXECUTING THROTTLE EVALUATION
def evaluate_throttle(
    state: str, message: str, is_loop: float | int | bool, step: int | None
) -> bool:
    """
    Evaluates step-based modulo intervals and time-delta elapsed durations to filter recurring events.

    Args:
        state: Current execution state string (e.g., 'running', 'done', 'fail').
        message: Unique identifier or message string used for temporal cache tracking.
        is_loop: Throttling threshold (boolean, interval integer, or time-delta float).
        step: Optional discrete step counter for modulo-based frequency throttling.

    Returns:
        bool: True if the event should be processed/logged, False if throttled.
    """
    # BYPASS CHECK: LOOP DISABLED
    # Returns True immediately if throttling/looping is disabled or falsy.
    if not is_loop:
        return True

    # TERMINAL STATE IDENTIFICATION
    # Identifies whether the current state represents a completion or failure condition,
    # which forces the throttle filter to allow the event through regardless of intervals.
    is_terminal_state = state.lower() in ["done", "fail"]

    # STEP-BASED THROTTLE: DISCRETE MILESTONE EVALUATION
    # Evaluates modulo-based milestone intervals if an explicit step counter is provided.
    if step is not None:
        interval = int(is_loop)
        is_due = (step == 0) or (step % interval == 0)

        if not is_due and not is_terminal_state:
            return False
    # TEMPORAL THROTTLE: TIME-DELTA DURATION EVALUATION
    # Evaluates elapsed wall-clock time against the loop threshold using a global cache map.
    else:
        now_ts = time.time()
        last_ts = float(LOOP_CACHE.get(message, 0.0))

        is_due = (now_ts - last_ts) >= float(is_loop)

        if not is_due and not is_terminal_state:
            return False

        LOOP_CACHE[message] = now_ts

    # EVENT APPROVAL
    # Returns True if the event is due for execution or represents an overriding terminal state.
    return True


# CACHE PURGE & MEMORY MANAGEMENT ENGINE
# This utility manages cache hygiene by removing completed or failed terminal state messages
# from the global tracking cache, preventing unbounded memory growth during long-running tasks.
# [>] EXECUTING CACHE CLEANUP & MEMORY PURGE
def cleanup_cache(state: str, message: str) -> None:
    """
    Removes terminal state messages from cache to prevent memory growth.

    Args:
        state: Current execution state string (e.g., 'running', 'done', 'fail').
        message: Unique message key corresponding to the entry stored in the global cache.
    """
    # STATE NORMALIZATION
    # Safely converts the input state string to lowercase, handling potential None values
    # to ensure robust comparison against terminal keywords.
    normalized_state = str(state or "").lower()

    # TERMINAL CACHE PURGE
    # Checks if the normalized state represents a completion or failure condition
    # and safely removes the message entry from the global cache if present.
    if normalized_state in ["done", "fail"] and message in LOOP_CACHE:
        LOOP_CACHE.pop(message, None)
