import queue
import subprocess
import threading
from typing import Any


# SYSTEM UTILITIES SUBSYSTEM: ASYNCHRONOUS STREAM DRAINER & TELEMETRY OBSERVER
# This utility deploys a background daemon observer thread to asynchronously drain process stdout
# into a thread-safe telemetry queue and manage proper stream closure.
# [>] EXECUTING STREAM DRAINER DEPLOYMENT
def start_stream_drainer(
    proc: "subprocess.Popen[Any] | None",
    out_q: "queue.Queue[str|None]",
) -> None:
    """
    Deploys a daemon observer thread to asynchronously drain output into the telemetry queue.

    Args:
        proc ("subprocess.Popen[Any] | None"): The active subprocess instance being monitored, or None.
        out_q ("queue.Queue[str|None]"): The thread-safe queue for telemetry output lines.

    Returns:
        None
    """

    # STREAM DRAINER WORKER DEFINITION
    # Defines the background worker function that continuously reads lines from process stdout
    # and pushes them into the thread-safe telemetry queue.
    def _stream_drainer() -> None:
        try:
            if proc and proc.stdout is not None:
                # STDOUT READ LOOP
                # Iterates line-by-line over active process stdout and pushes non-empty lines to the queue.
                for line in iter(proc.stdout.readline, ""):
                    if line:
                        out_q.put(line)
        finally:
            # TERMINATION SIGNAL & STDOUT RESOURCE CLEANUP
            # Signals end-of-stream by pushing None to the queue and safely closing the process stdout pipe.
            out_q.put(None)
            if proc and proc.stdout:
                try:
                    proc.stdout.close()
                except OSError:
                    pass

    # DAEMON THREAD LAUNCH OR IMMEDIATE STREAM TERMINATION
    # Spawns a daemon telemetry monitor thread if valid process stdout is available;
    # otherwise, immediately signals stream exhaustion via the output queue.
    if proc and proc.stdout is not None:
        monitor_thread = threading.Thread(target=_stream_drainer, daemon=True)
        monitor_thread.start()
    else:
        out_q.put(None)
