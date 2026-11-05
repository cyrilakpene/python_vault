import signal
import sys
from typing import Callable

from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: SIGNAL INTERCEPTION & GRACEFUL SHUTDOWN HANDLER
# This utility intercepts incoming operating system termination signals, logs shutdown warnings,
# and safely executes registered cleanup callbacks once before terminating the process.
# [>] EXECUTING SIGNAL INTERCEPTION & GRACEFUL SHUTDOWN
def intercept_signal(
    signum: int,
    _frame: object | None,
    cleanup_callback: Callable[[], None],
    get_has_run: Callable[[], bool],
    set_has_run: Callable[[], None],
) -> None:
    """
    Intercepts incoming operating system signals, logs shutdown warnings,
    and executes the cleanup callback safely before terminating the process.

    Args:
        signum (int): The numerical signal identifier received by the process.
        _frame (object | None): The current stack frame object at the time of signal delivery.
        cleanup_callback (Callable[[], None]): A callable function to execute during graceful shutdown.
        get_has_run (Callable[[], bool]): A getter function checking whether cleanup has already executed.
        set_has_run (Callable[[], None]): A setter function marking cleanup as executed.

    Returns:
        None
    """
    # SIGNAL RESOLUTION & SHUTDOWN WARNING REPORT
    # Resolves the human-readable signal name from the signal number and reports a warning status.
    signal_name = signal.Signals(signum).name
    report_status(
        state="warn",
        message=f"Received signal {signal_name} ({signum}). Initiating graceful shutdown...",
        context=LogContext(
            component="security.shutdown",
            log_path=log_path,
            silent=True,
            trace_id="shutdown",
            actor=context.get("user"),
            payload={"signal_name": signal_name, "signum": signum},
        ),
    )

    # DUPLICATE EXECUTION GUARD & CLEANUP EXECUTION
    # Checks if cleanup has already been executed to prevent re-entrancy,
    # then invokes the cleanup callback within a safe exception-handling block.
    if not get_has_run():
        set_has_run()
        try:
            cleanup_callback()
        except Exception as err:
            report_status(
                state="warn",
                message=f"Error during shutdown callback: {err}",
                context=LogContext(
                    component="security.shutdown",
                    log_path=log_path,
                    silent=True,
                    trace_id="shutdown",
                    actor=context.get("user"),
                    exception=str(err),
                    payload={"signal_name": signal_name, "signum": signum},
                ),
            )
        finally:
            # PROCESS TERMINATION
            # Terminates the process cleanly with a standard zero exit code.
            sys.exit(0)
