import shlex
import subprocess
import sys
from typing import Any

from .exceptions import (
    CommandFailedError,  # type: ignore[import-not-found]
    CommandTimeoutError,  # type: ignore[import-not-found]
    PathResolutionError,  # type: ignore[import-not-found]
    UserCancelError,  # type: ignore[import-not-found]
)
from .constants import report_status, log_path  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: PROCESS CLEANUP & MEMORY SANITIZATION
# This utility ensures child process termination with timeout-based escalation to forceful killing,
# and securely zero-fills sensitive captured byte buffers in memory.
# [>] EXECUTING PROCESS CLEANUP & MEMORY ZEROING
def handle_process_cleanup(
    proc: subprocess.Popen[Any] | None,
    captured_byte_buffer: bytearray,
) -> None:
    """
    Ensures child process termination and securely clears captured memory buffer.

    Args:
        proc (subprocess.Popen[Any] | None): The active subprocess handle to terminate, or None.
        captured_byte_buffer (bytearray): The mutable byte buffer containing captured stream data to sanitize.

    Returns:
        None
    """
    # PROCESS TERMINATION & TIMEOUT ESCALATION
    # Checks if the subprocess is still running, requests graceful termination,
    # and escalates to forceful termination if the timeout expires.
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

    # SENSITIVE BUFFER ZERO-FILL SANITIZATION
    # Overwrites every byte in the captured buffer with zeros to clear sensitive data from memory.
    for i in range(len(captured_byte_buffer)):
        captured_byte_buffer[i] = 0


# SYSTEM UTILITIES SUBSYSTEM: EXECUTION EXCEPTION INTERCEPTION & MAPPING
# This utility intercepts standard subprocess, file, and interrupt exceptions, logs status events,
# and maps them to descriptive, domain-specific custom exceptions.
# [>] EXECUTING EXCEPTION MAPPING & INTERCEPTION
def handle_execution_exceptions(e: Exception, _cmd: list[str]) -> None:
    """
    Intercepts and maps execution exceptions to custom domain errors with status logging.

    Args:
        e (Exception): The caught exception object raised during command execution.
        _cmd (list[str]): The command list associated with the execution context.

    Returns:
        None

    Raises:
        CommandTimeoutError: If the subprocess execution exceeded its time limit.
        CommandFailedError: If the subprocess exited with a non-zero return code.
        PathResolutionError: If the target executable file or path cannot be found.
        UserCancelError: If the execution was interrupted by the user.
        Exception: Re-raises any unhandled exception.
    """
    # TIMEOUT EXCEPTION INTERCEPTION
    # Logs a warning status for timed-out processes and raises a custom CommandTimeoutError.
    if isinstance(e, subprocess.TimeoutExpired):
        report_status(
            state="warn",
            message=f"Command killed after {e.timeout}s -> {shlex.join(e.cmd)}",
            log_path=log_path,
        )
        raise CommandTimeoutError(timeout=e.timeout, cmd=e.cmd) from e

    # CALLED PROCESS ERROR INTERCEPTION
    # Maps non-zero exit codes directly to a custom CommandFailedError.
    elif isinstance(e, subprocess.CalledProcessError):
        raise CommandFailedError(returncode=e.returncode, cmd=e.cmd) from e

    # FILE NOT FOUND ERROR INTERCEPTION
    # Logs a warning status for missing binaries or paths and raises a custom PathResolutionError.
    elif isinstance(e, FileNotFoundError):
        report_status(
            state="warn", message=f"File not found: {e.filename}", log_path=log_path
        )
        raise PathResolutionError(filename=str(e.filename)) from e

    # KEYBOARD INTERRUPT EXCEPTION INTERCEPTION
    # Writes a newline, logs a cancellation status warning, and raises a clean UserCancelError.
    elif isinstance(e, KeyboardInterrupt):
        sys.stdout.write("\n")
        report_status(state="warn", message=str(UserCancelError()), log_path=log_path)
        raise UserCancelError from None

    # UNHANDLED EXCEPTION RE-RAISING
    # Propagates any other unrecognized exception up the call stack.
    raise e
