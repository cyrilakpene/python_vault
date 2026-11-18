import sys
import tty
import queue
import signal
import select
import termios
import subprocess
from typing import Any, cast, Generator
from contextlib import contextmanager

from .reader import read_line, read_all  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# SESSION INTERFACE ABSTRACTION: NON-BLOCKING TELEMETRY BRIDGE
# This interface serves as the primary communication bridge between the host application and isolated workers.
# Remote process monitors, background execution managers, and live output stream parsers depend
# explicitly on this class to poll process states and extract stdout/stderr feeds without execution stalls.
class SessionInterface:
    """
    A high-level handle for interacting with a managed subprocess.

    Provides non-blocking access to consolidated stdout/stderr streams. This gateway mandates
    thread-safe queue handling, asynchronous stream extraction, and deterministic process lifecycle
    management to guarantee safe polling and non-blocking inter-process communication.
    """

    # STREAMING ENGINE SUBSYSTEM: PROCESS READER INITIALIZATION
    # This initializer sets up the streaming process reader, binding the active subprocess handle,
    # the thread-safe output queue for asynchronous message passing, and an exhaustion tracking flag.
    def __init__(
        self,
        proc: "subprocess.Popen[Any]",
        out_queue: "queue.Queue[str|None]",
    ) -> None:
        """
        Initializes the streaming process reader with a subprocess handle and output queue.

        Args:
            proc (subprocess.Popen[Any]): The active subprocess handle being monitored and read.
            out_queue (queue.Queue[str | None]): Thread-safe queue for asynchronous output string streaming.
        """
        # SUBPROCESS & QUEUE BINDING
        # Store the target subprocess handle and output communication queue.
        self.proc: "subprocess.Popen[Any]" = proc
        self._out_queue: "queue.Queue[str|None]" = out_queue

        # EXHAUSTION FLAG INITIALIZATION
        # Initialize the exhaustion tracking flag to False, indicating an active, unconsumed stream state.
        self._is_exhausted: bool = False

    # STREAMING ENGINE SUBSYSTEM: ASYNC PROCESS OUTPUT READING
    # This method retrieves the next line of output from the process stream by delegating
    # to an external line-reading utility, managing queue retrieval and type casting safely.
    def read_line(self) -> str | None:
        """
        Retrieves the next line of output from the stream if available, else returns None.

        Returns:
            str | None: The next output line string, or None if the stream is exhausted or empty.
        """
        # STREAMING DELEGATION: EXTERNAL READ_LINE INVOCATION
        # Delegate thread-safe queue consumption and line extraction to the centralized read_line utility,
        # casting the output queue to match expected typing protocols.
        return read_line(cast("queue.Queue[str] | None", self._out_queue))

    # STREAMING ENGINE SUBSYSTEM: ASYNC PROCESS OUTPUT DRAINAGE
    # This method drains all currently buffered telemetry lines or output strings from the process stream
    # by delegating to an external drainage utility, managing stream exhaustion state safely.
    def read_all(self) -> list[str]:
        """
        Drains all currently buffered telemetry lines from the session.

        Returns:
            list[str]: A list containing all drained output lines from the stream buffer.
        """
        # STREAMING DELEGATION: EXTERNAL READ_ALL INVOCATION
        # Delegate complete buffer drainage and exhaustion state tracking
        # to the centralized read_all utility, passing the exhaustion flag and the casted output queue.
        return read_all(
            self._is_exhausted,
            cast("queue.Queue[str] | None", self._out_queue),
        )

    # STREAMING ENGINE SUBSYSTEM: SUBPROCESS HEALTH INSPECTION
    # This method checks whether the underlying monitored subprocess is still actively running
    # by polling its exit status code via the process handle.
    def is_alive(self) -> bool:
        """
        Checks if the underlying subprocess is still running.

        Returns:
            bool: True if the process is still running (exit code is None), False if it has terminated.
        """
        # PROCESS POLL & LIVENESS EVALUATION
        # Query the operating system process status via poll().
        # A return value of None indicates the process is still executing.
        return self.proc.poll() is None

    # PROCESS CONTROL SUBSYSTEM: SESSION PROCESS SUSPENSION
    # PROCESS CONTROL SUBSYSTEM: SESSION PROCESS SUSPENSION
    # This method verifies the session process handle and liveness, then dispatches the SIGSTOP signal
    # to freeze execution while recording structured audit telemetry.
    def pause(self) -> None:
        """
        Pauses the active session process by verifying its existence and liveness,
        then transmitting a SIGSTOP signal and reporting status telemetry.
        """
        # PROCESS EXISTENCE & LIVENESS VERIFICATION
        # Check if the process handle is instantiated and actively running before issuing signals.
        if self.proc and self.is_alive():
            # SIGSTOP SIGNAL DISPATCH
            # Send the SIGSTOP signal directly to the underlying subprocess to freeze its execution state.
            try:
                import os

                os.killpg(os.getpgid(self.proc.pid), signal.SIGSTOP)
            except (ProcessLookupError, PermissionError, OSError):
                self.proc.send_signal(signal.SIGSTOP)

            # AUDIT TELEMETRY REPORTING
            # Report the suspension status via the structured logging system, capturing process ID and metadata.
            report_status(
                state="warn",
                message="Session process paused via SIGSTOP.",
                context=LogContext(
                    component="security.open_secure_session",
                    log_path=log_path,
                    silent=True,
                    trace_id="open_secure_session",
                    actor=context.get("user"),
                    payload={"signal": "SIGSTOP", "pid": self.proc.pid},
                ),
            )

    # PROCESS CONTROL SUBSYSTEM: SESSION PROCESS RESUMPTION
    # This method verifies the session process handle exists, dispatches the SIGCONT signal
    # to resume frozen execution, and records structured audit telemetry.
    def resume(self) -> None:
        """
        Resumes the paused session process by verifying its existence,
        transmitting a SIGCONT signal, and reporting status telemetry.
        """
        # PROCESS EXISTENCE VERIFICATION
        # Check if the process handle is instantiated before issuing resume signals.
        if self.proc:
            # SIGCONT SIGNAL DISPATCH
            # Send the SIGCONT signal directly to the underlying subprocess to resume its execution state.
            try:
                import os

                os.killpg(os.getpgid(self.proc.pid), signal.SIGCONT)
            except (ProcessLookupError, PermissionError, OSError):
                self.proc.send_signal(signal.SIGCONT)

            # AUDIT TELEMETRY REPORTING
            # Report the resumption status via the structured logging system, capturing process ID and metadata.
            report_status(
                state="info",
                message="Session process resumed via SIGCONT.",
                context=LogContext(
                    component="security.open_secure_session",
                    log_path=log_path,
                    silent=True,
                    trace_id="open_secure_session",
                    actor=context.get("user"),
                    payload={"signal": "SIGCONT", "pid": self.proc.pid},
                ),
            )


# SECURITY SUBSYSTEM: INTERACTIVE MONITOR & SESSION PAUSE CONTROLLER
# This context manager configures terminal cbreak mode for single-character reads and provides
# a non-blocking polling helper to interactively pause and resume secure sessions via keystrokes.
# [>] EXECUTING INTERACTIVE MONITOR CONTEXT MANAGER
@contextmanager
def interactive_monitor(
    session: SessionInterface,
    pause_key: str = "p",
    resume_key: str = "r",
    pause_msg: str = "[Process Paused]",
    resume_msg: str = "[Process Resumed]",
) -> Generator[Any, None, None]:
    """
    Context manager that configures terminal cbreak mode and provides a polling helper
    to pause and resume a secure session interactively via keystrokes.

    Args:
        session (SessionInterface): The active secure session interface being monitored.
        pause_key (str): The keystroke character used to trigger a session pause. Defaults to "p".
        resume_key (str): The keystroke character used to trigger a session resume. Defaults to "r".
        pause_msg (str): Status message logged when the process is paused. Defaults to "[Process Paused]".
        resume_msg (str): Status message logged when the process is resumed. Defaults to "[Process Resumed]".

    Yields:
        MonitorState: A state container instance providing polling capabilities for live key inputs.
    """
    old_stdin_settings = None
    is_tty = sys.stdin.isatty()

    # TERMINAL TTY CONFIGURATION & CBREAK SETUP
    # Configures standard input for non-blocking single-character terminal reads if a valid TTY is present.
    if is_tty:
        try:
            old_stdin_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except termios.error:
            pass

    # MONITOR STATE CONTAINER CLASS
    # Encapsulates pause states and provides non-blocking stdin polling methods for keystroke evaluation.
    class MonitorState:
        def __init__(self):
            self.is_paused = False

        def poll(self) -> bool:
            """
            Polls standard input non-blockingly for pause or resume keystrokes.

            Returns:
                bool: True if a pause or resume signal was successfully processed, otherwise False.
            """
            if not is_tty:
                return False

            # NON-BLOCKING STDIN SELECT CHECK
            # Checks for available input data on stdin using a zero-timeout select call.
            if sys.stdin in select.select([sys.stdin], [], [], 0.0)[0]:
                key_input = sys.stdin.read(1).lower()

                # PAUSE KEYSTROKE EVALUATION & SIGNAL LOGGING
                # Pauses the secure session, sets pause state, and logs SIGSTOP telemetry.
                if key_input == pause_key.lower() and not self.is_paused:
                    session.pause()
                    self.is_paused = True
                    if pause_msg:
                        report_status(
                            state=None,
                            message=f"\n{pause_msg}",
                            context=LogContext(
                                component="security.open_secure_session",
                                log_path=log_path,
                                trace_id="open_secure_session",
                                actor=context.get("user"),
                                payload={"signal": "SIGSTOP"},
                            ),
                        )
                    return True

                # RESUME KEYSTROKE EVALUATION & SIGNAL LOGGING
                # Resumes the secure session, clears pause state, and logs SIGCONT telemetry.
                elif key_input == resume_key.lower() and self.is_paused:
                    session.resume()
                    self.is_paused = False
                    if resume_msg:
                        report_status(
                            state=None,
                            message=resume_msg,
                            context=LogContext(
                                component="security.open_secure_session",
                                log_path=log_path,
                                trace_id="open_secure_session",
                                actor=context.get("user"),
                                payload={"signal": "SIGCONT"},
                            ),
                        )
                    return True
            return False

    # CONTEXT YIELD & TERMINAL RESTORATION FINALLY BLOCK
    # Yields the monitor state container to the block and restores original terminal settings on exit.
    try:
        yield MonitorState()
    finally:
        if old_stdin_settings is not None and is_tty:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_stdin_settings)
            except termios.error:
                pass
