from typing import Callable, Iterable

from .handler import GracefulShutdownHandler  # type: ignore[import-not-found]
from .signals import default_signals  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: SHUTDOWN SIGNAL REGISTRATION FACTORY
# This utility serves as a factory helper to instantiate, bind,
# and register graceful shutdown handlers for process termination signals.
# [>] EXECUTING SHUTDOWN SIGNAL REGISTRATION
def register_shutdown_signals(
    lock_callback: Callable[[], None], signals: Iterable[int] = default_signals
) -> GracefulShutdownHandler:
    """
    Factory helper to quickly bind and register a cleanup callback for shutdown signals.

    Args:
        lock_callback (Callable[[], None]): The cleanup callback function to invoke upon shutdown.
        signals (Iterable[int], optional): An iterable collection of signals to handle. Defaults to default_signals.

    Returns:
        GracefulShutdownHandler: The initialized and registered shutdown handler instance.
    """
    # HANDLER INSTANTIATION & REGISTRATION
    # Instantiates the GracefulShutdownHandler with the cleanup callback and target signals,
    # triggers registration, and returns the active handler instance.
    handler = GracefulShutdownHandler(
        cleanup_callback=lock_callback, handled_signals=signals
    )
    handler.register()
    return handler
