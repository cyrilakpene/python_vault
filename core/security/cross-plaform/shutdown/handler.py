from typing import Callable, Iterable

from .signals import default_signals  # type: ignore[import-not-found]
from .interceptor import intercept_signal  # type: ignore[import-not-found]
from .registration import register_signal_handlers  # type: ignore[import-not-found]


# SIGNAL TRAPPING & CLEANUP ORCHESTRATION LAYER
# CONCRETE CONTROLLER: IDEMPOTENT PROCESS TERMINATION ENGINE
# Encapsulates OS signal trapping (SIGINT, SIGTERM) to execute thread-safe, single-execution cleanup callbacks.
# By intercepting shutdown signals, it guarantees graceful resource releases, prevents database corruption,
# and eliminates hanging process threads during forced or unexpected lifecycle terminations.
class GracefulShutdownHandler:
    """Encapsulates OS signal trapping for thread-safe, idempotent cleanup callbacks.

    Ensures registered cleanup callbacks run exactly once upon receiving OS signals,
    preventing resource leaks, corrupted state, and hanging process threads.
    """

    # GRACEFUL SHUTDOWN SUBSYSTEM: SIGNAL HANDLER INITIALIZATION
    # This initializer sets up the graceful shutdown manager, binding the cleanup callback,
    # specifying the monitored operating system signals, and initializing an idempotency guard
    # to prevent duplicate cleanup execution during termination sequences.
    def __init__(
        self,
        cleanup_callback: Callable[[], None],
        handled_signals: Iterable[int] = default_signals,
    ) -> None:
        """
        Initializes the signal handler and cleanup manager with a callback and target signals.

        Args:
            cleanup_callback (Callable[[], None]): The callable function executed upon receiving a termination signal.
            handled_signals (Iterable[int], optional): Collection of OS signal integers to listen for. Defaults to default_signals.
        """
        # CALLBACK & SIGNAL BINDING
        # Store the provided cleanup routine and the target signals to monitor.
        self._cleanup_callback = cleanup_callback
        self._handled_signals = handled_signals

        # IDEMPOTENCY GUARD INITIALIZATION
        # Initialize execution tracking to ensure cleanup routines are triggered at most once.
        self._has_run = False

    # GRACEFUL SHUTDOWN SUBSYSTEM: IDEMPOTENCY STATUS INSPECTION
    # This internal method provides read-only access to the execution state flag,
    # ensuring callers can verify whether the cleanup sequence has already been triggered.
    def _get_has_run(self) -> bool:
        """
        Retrieves the current execution status of the shutdown sequence.

        Returns:
            bool: True if cleanup has already been executed, False otherwise.
        """
        # STATE INSPECTION
        # Return the boolean idempotency flag indicating whether cleanup has run.
        return self._has_run

    # GRACEFUL SHUTDOWN SUBSYSTEM: IDEMPOTENCY STATE MUTATION
    # This internal method updates the execution state flag to True, locking the cleanup
    # sequence to enforce idempotency and prevent duplicate termination executions.
    def _set_has_run(self) -> None:
        """
        Marks the shutdown sequence as executed, updating the idempotency flag.
        """
        # STATE MUTATION
        # Set the execution tracking flag to True to prevent redundant cleanup calls.
        self._has_run = True

    # GRACEFUL SHUTDOWN SUBSYSTEM: OS SIGNAL INTERCEPTION & TEARDOWN DELEGATION
    # This method intercepts operating system termination signals and delegates the teardown
    # and cleanup coordination to an external interceptor utility, supplying the cleanup callback
    # and idempotency state management functions.
    def _signal_handler(self, signum: int, _frame: object | None) -> None:
        """
        Intercepts incoming operating system signals and delegates teardown to an external utility.

        Args:
            signum (int): The operating system signal number received (e.g., SIGINT, SIGTERM).
            _frame (object | None): The current stack frame at the time of signal interception.
        """
        # SIGNAL DELEGATION: EXTERNAL INTERCEPT_SIGNAL INVOCATION
        # Delegate signal logging, idempotency verification, and callback execution
        # to the centralized intercept_signal utility, passing the signal number, stack frame,
        # cleanup callback, and idempotency getter/setter methods.
        intercept_signal(
            signum=signum,
            _frame=_frame,
            cleanup_callback=self._cleanup_callback,
            get_has_run=self._get_has_run,
            set_has_run=self._set_has_run,
        )

    # GRACEFUL SHUTDOWN SUBSYSTEM: OS SIGNAL HANDLER REGISTRATION
    # This method registers the configured operating system signals with the Python runtime,
    # binding them to the internal signal handler by delegating to an external registration utility.
    def register(self) -> None:
        """
        Registers the shutdown signal handlers with the operating system by delegating to a modular registration utility.
        """
        # SIGNAL REGISTRATION DELEGATION: EXTERNAL REGISTER_SIGNAL_HANDLERS INVOCATION
        # Delegate signal binding and exception handling setup to the centralized register_signal_handlers utility,
        # passing the monitored signals collection and the internal signal handler callback.
        register_signal_handlers(
            handled_signals=self._handled_signals,
            handler_callback=self._signal_handler,
        )
