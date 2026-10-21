import signal
import sys
from typing import Callable, Iterable

from interface.report_status import report_status  # type: ignore[import-not-found]
from security.runtime_context import log_path  # type: ignore[import-not-found]

# CROSS-PLATFORM TERMINATION SIGNALS
# Defines standard graceful shutdown signals for process management.
default_signals: tuple[signal.Signals, ...] = (
    signal.SIGINT,  # Keyboard interrupt (Ctrl+C)
    signal.SIGTERM,  # Standard termination request
)

# UNIX HUP INTEGRATION (TERMINAL DISCONNECT)
# Appends SIGHUP if available on the host platform to catch terminal closure.
if hasattr(signal, "SIGHUP"):
    default_signals += (signal.SIGHUP,)  # Hangup signal for session detachment


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

    # SIGNAL MANAGEMENT SUBSYSTEM: GRACEFUL SHUTDOWN HANDLER INITIALIZER
    # This class constructor initializes a robust signal/cleanup manager that intercepts
    # operating system termination signals (e.g., SIGINT, SIGTERM) to execute safe teardown routines,
    # ensuring resource cleanup and preventing orphaned background processes.
    def __init__(
        self,
        cleanup_callback: Callable[[], None],
        handled_signals: Iterable[int] = default_signals,
    ) -> None:
        """
        Initialize the graceful shutdown handler with a cleanup callback and target signal bindings.

        Args:
            cleanup_callback (Callable[[], None]): A callable routine executed during system shutdown or signal interception.
            handled_signals (Iterable[int], optional): Collection of OS signal integers to intercept. Defaults to default_signals.
        """
        # CLEANUP CALLBACK BINDING
        # Store the provided cleanup callback function reference for execution upon signal interception.
        self._cleanup_callback = cleanup_callback

        # SIGNAL COLLECTION BINDING
        # Store the target signal integers (e.g., SIGINT, SIGTERM) to be monitored.
        self._handled_signals = handled_signals

        # EXECUTION GUARD FLAG INITIALIZATION
        # Tracks whether the teardown sequence has already been executed to ensure idempotent cleanup.
        self._has_run = False

    # SIGNAL MANAGEMENT SUBSYSTEM: OS SIGNAL INTERCEPTION & SHUTDOWN ORCHESTRATION
    # This event handler intercepts operating system termination signals (e.g., SIGINT, SIGTERM),
    # logs the signal telemetry, enforces idempotent execution using an internal guard flag,
    # safely invokes the registered cleanup callback, and exits the application with status 0.
    def _signal_handler(self, signum: int, _frame: object | None) -> None:
        """
        SIGNAL HANDLER HOOK: OS TERMINATION INTERCEPTION & TEARDOWN ROUTINE
        Intercepts incoming operating system signals, resolves their symbolic names, logs shutdown warnings,
        and executes the cleanup callback safely before terminating the process.

        Args:
            signum (int): The integer value of the intercepted operating system signal.
            _frame (object | None): The current stack frame object at the time the signal was received.
        """
        # SIGNAL IDENTIFICATION & TELEMETRY REPORTING
        # Resolve the symbolic signal name from its integer value and log a warning status for shutdown initiation
        signal_name = signal.Signals(signum).name
        report_status(
            state="warn",
            message=f"Received signal {signal_name} ({signum}). Initiating graceful shutdown...",
            silent=True,
            log_path=log_path,
        )

        # IDEMPOTENCY GUARD & EXECUTION FLAG STAMPING
        # Verify that the shutdown sequence has not already been executed; mark execution flag if clear
        if not self._has_run:
            self._has_run = True
            try:
                # CLEANUP CALLBACK EXECUTION & EXCEPTION SHIELDING
                # Execute the registered teardown routine, catching and logging any exceptions to prevent crash loops
                self._cleanup_callback()
            except Exception as err:
                report_status(
                    state="warn",
                    message=f"Error during shutdown callback: {err}",
                    silent=True,
                    log_path=log_path,
                )
            finally:
                # CLEAN PROCESS TERMINATION
                # Terminate the application lifecycle cleanly with exit code 0
                sys.exit(0)

    # SIGNAL MANAGEMENT SUBSYSTEM: SIGNAL REGISTRATION & HANDLER ACTIVATION
    # This method registers the shutdown handler across all specified operating system signals
    # within the main thread. It includes exception shielding to safely handle platform limitations
    # or execution outside the main thread.
    def register(self) -> None:
        """
        REGISTRATION HOOK: SIGNAL HANDLER ACTIVATION
        Iterates through configured signal integers, binding each to the internal shutdown handler
        while catching platform or threading errors gracefully.
        """
        # SIGNAL COLLECTION ITERATION
        # Iterate over each target signal integer designated for monitoring
        for sig in self._handled_signals:
            try:
                # SIGNAL BINDING & EXCEPTION SHIELDING
                # Register the signal handler callback; catch ValueError/OSError if invoked outside
                # the main thread or on an unsupported operating system platform
                signal.signal(sig, self._signal_handler)
            except (ValueError, OSError) as err:
                report_status(
                    state="warn",
                    message=f"Could not register signal handler for {sig}: {err}",
                    silent=True,
                    log_path=log_path,
                )


# SIGNAL HANDLER FACTORY ENGINE: GRACEFUL SHUTDOWN REGISTRATION
# This utility encapsulates the setup and registration lifecycle for
# asynchronous OS signal handling, ensuring atomic cleanup actions
# are executed smoothly during termination requests.
def register_shutdown_signals(
    lock_callback: Callable[[], None], signals: Iterable[int] = default_signals
) -> GracefulShutdownHandler:
    """Factory helper to quickly bind and register a cleanup callback for shutdown signals.

    Args:
        lock_callback: Callable function to execute during cleanup.
        signals: Iterable of signal integers to monitor and handle.

    Returns:
        A registered GracefulShutdownHandler instance.
    """

    # HANDLER INSTANTIATION & CALLBACK INJECTION
    # Binds the user-supplied cleanup logic and targeted signal tuple
    # to the core GracefulShutdownHandler state machine.
    handler = GracefulShutdownHandler(
        cleanup_callback=lock_callback, handled_signals=signals
    )

    # OS SIGNAL HOOK ACTIVATION
    # Registers the signal interception hooks with the underlying Python
    # runtime environment to catch interrupt and termination vectors.
    handler.register()

    # ACTIVE HANDLER EMISSION
    # Returns the fully configured and armed shutdown handler instance.
    return handler
