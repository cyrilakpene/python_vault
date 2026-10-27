import signal
from typing import Callable, Iterable

from .constants import report_status, log_path  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: SIGNAL HANDLER REGISTRATION & BINDING
# This utility iterates through configured signal identifiers, safely binding each to the designated
# shutdown handler callback while catching platform-specific registration exceptions.
# [>] EXECUTING SIGNAL HANDLER REGISTRATION
def register_signal_handlers(
    handled_signals: Iterable[int],
    handler_callback: Callable[[int, object | None], None],
) -> None:
    """
    Iterates through configured signal integers, binding each to the shutdown handler callback.

    Args:
        handled_signals (Iterable[int]): An iterable collection of numerical signal identifiers to bind.
        handler_callback (Callable[[int, object | None], None]): The callback function to invoke upon receiving each signal.

    Returns:
        None
    """
    # SIGNAL BINDING ITERATION & EXCEPTION HANDLING
    # Iterates over each signal in the collection, attempting to register the signal handler
    # and gracefully logging warnings if platform restrictions or invalid signals prevent binding.
    for sig in handled_signals:
        try:
            signal.signal(sig, handler_callback)
        except (ValueError, OSError) as err:
            report_status(
                state="warn",
                message=f"Could not register signal handler for {sig}: {err}",
                silent=True,
                log_path=log_path,
            )
