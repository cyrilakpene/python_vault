import queue
import subprocess
from typing import Any, cast

from .reader import read_line, read_all  # type: ignore[import-not-found]


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
