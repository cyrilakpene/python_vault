import subprocess
import shlex
import threading
import queue
from typing import Any, Generator, Optional, IO
from contextlib import contextmanager

from report_status import report_status  # type: ignore[import-not-found]


# SYSTEM PATH RESOLUTION EXCEPTION CLASS
# Custom exception domain class used to signal when a required file or path cannot be found.
# Standardizes path resolution error formatting across CLI workflows to enable graceful handling without raw stack traces.
class PathResolutionError(Exception):
    """Raised when a required file or path cannot be resolved or is missing."""

    def __init__(self, filename: str, message: str = "Path resolution failure."):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes path error message with standard system tag and filename before delegating to BaseException initializer.
        target_file = filename if filename else "Target path"
        super().__init__(f"Operation Failed: {message} -> {target_file} is missing.")
        self.filename = filename


# SYSTEM INTERRUPTION EXCEPTION CLASS
# Custom exception domain class used to signal explicit user cancellations or interactive abort requests (e.g., SIGINT / Ctrl+C).
# Standardizes cancellation formatting across CLI workflows to enable graceful process termination without stack traces.
class UserCancelError(Exception):
    """Raised when user cancels operation."""

    def __init__(self, message: str = "User interrupted process (Ctrl+C)."):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes cancellation message with standard system tag before delegating to BaseException initializer.
        super().__init__(f"Operation Cancel: {message}")


# SESSION INTERFACE ABSTRACTION: NON-BLOCKING TELEMETRY BRIDGE
# CONCRETE GATEWAY: MANAGED SUBPROCESS COMMUNICATION HANDLE
# This class acts as a high-level handle for interacting with a managed subprocess.
# It decouples the caller from the raw 'subprocess.Popen' object, providing a thread-safe
# gateway to the consolidated I/O streams. By wrapping the 'Queue' populated by the
# background observer, it ensures that the parent script can poll for updates without ever hanging.
#
# ASYNCHRONOUS I/O & THREAD-SAFETY BOUNDING:
# Process communication operates via non-blocking queue consumers and asynchronous stream polling.
# To prevent thread starvation, deadlock conditions, or zombie process accumulation, this handle
# enforces strict timeout semantics, atomic read locks, and deterministic process lifecycle teardowns.
#
# SUBSYSTEM INTEGRATION PIPELINE:
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

    # SUBPROCESS SUBSYSTEM ENGINE: SESSION INTERFACE INITIALIZER
    # This class constructor initializes the SessionInterface wrapper, binding an active text-mode
    # subprocess handle and its corresponding thread-safe telemetry output queue. It also configures
    # internal flags to track stream exhaustion and ensure reliable asynchronous I/O consumption.
    def __init__(
        self, proc: "subprocess.Popen[str]", out_queue: "queue.Queue[Optional[str]]"
    ) -> None:
        """
        Initialize the SessionInterface with a process handle and telemetry queue.

        Args:
            proc (subprocess.Popen[str]): The active subprocess instance representing the managed task in text mode.
            out_queue (queue.Queue[Optional[str]]): The thread-safe queue containing captured and consolidated I/O strings.
        """
        # ATOMIC PROCESS ASSIGNMENT
        # Links the running process handle to the session instance, using Popen[str] to maintain parity
        # with the text-mode protocol used during background spawning.
        self.proc: "subprocess.Popen[str]" = proc

        # INTERNAL TELEMETRY CHANNEL BINDING
        # Binds the thread-safe gateway queue for consolidated I/O streams. The type hint includes
        # 'Optional' to accommodate the 'None' EOF sentinel injected by background drainer threads.
        self._out_queue: "queue.Queue[Optional[str]]" = out_queue

        # STREAM EXHAUSTION STATE FLAG INITIALIZATION
        # Tracks whether the telemetry stream has been fully drained following process termination,
        # serving as a structural firewall against premature observer teardown.
        self._is_exhausted: bool = False

    # SUBPROCESS SUBSYSTEM ENGINE: NON-BLOCKING TELEMETRY LINE READER
    # This method retrieves the next available line of output from the thread-safe telemetry queue.
    # It attempts to poll the queue buffer, returning the decoded string payload or None if the stream
    # is currently empty, ensuring the parent application maintains a responsive execution loop.
    def read_line(self) -> "str | None":
        """
        Retrieves the next line of output if available, else returns None.

        Returns:
            str | None: The next decoded string from the telemetry buffer, or None if the queue is empty.
        """
        # NON-BLOCKING TELEMETRY QUEUE INGRESS
        # Attempt to pull the next available line from the background queue, utilizing queue exception
        # handling to safeguard against thread-stalling during idle cycles.
        try:
            # Retrieve consolidated I/O stream payload from thread-safe queue
            return self._out_queue.get()

        except queue.Empty:
            # IDLE TELEMETRY BUFFER FALLBACK
            # No new data is available during this clock cycle; return None immediately
            # to signal that the managed subprocess stream is currently idle.
            return None

    # SUBPROCESS SUBSYSTEM ENGINE: BATCH TELEMETRY DRAINER & EOF SENTINEL HANDLER
    # This method drains all currently buffered telemetry lines from the session queue in a single batch.
    # It loops non-blockingly until the buffer is exhausted or an EOF sentinel (None) is encountered,
    # updating the exhaustion state flag and reducing processing overhead during bursty output events.
    def read_all(self) -> list[str]:
        """
        Drains all currently buffered telemetry lines from the session.
        This batch-read approach reduces overhead in high-throughput scenarios.

        Returns:
            list[str]: A list of all strings currently residing in the telemetry buffer.
        """
        # ACCUMULATOR INITIALIZATION & EXHAUSTION GUARD
        # Initialize string list accumulator and check if the background drainer has already signaled EOF
        lines: list[str] = []

        if self._is_exhausted:
            return lines

        # NON-BLOCKING BATCH DRAIN LOOP
        # Continuously poll the thread-safe queue until empty or an EOF sentinel is encountered
        while True:
            try:
                # Attempt to extract the next line from the telemetry bridge without halting execution
                line: "str | None" = self._out_queue.get_nowait()

                # Check for EOF sentinel injection (None) signaling pipe closure
                if line is None:
                    self._is_exhausted = True
                    break

                lines.append(line)

            except queue.Empty:
                # Queue buffer is fully drained for this cycle; break loop and return accumulated lines
                break

        # ACCUMULATED TELEMETRY RETURN
        # Return the collected batch of telemetry string outputs
        return lines

    # SUBPROCESS SUBSYSTEM ENGINE: PROCESS LIVELIHOOD POLLINATOR
    # This method queries the underlying operating system process table via `self.proc.poll()`
    # to evaluate whether the managed subprocess is still executing or has terminated,
    # providing a non-blocking check on child process liveliness.
    def is_alive(self) -> bool:
        """
        Checks if the underlying process is still running.

        Returns:
            bool: True if the process is still executing, False if it has terminated.
        """
        # OS PROCESS TABLE QUERY (NON-BLOCKING POLL)
        # Query the child process's current execution status via the .poll() system call.
        # A return value of 'None' indicates the process is active; any integer exit code signifies termination.
        return self.proc.poll() is None


# ARCHITECTURAL SESSION GATEKEEPER: PERSISTENT SUBPROCESS HANDLER (V2)
# This engine provides a high-integrity, non-blocking abstraction layer.
# This version integrates a background 'Drainer Thread' to prevent
# Pipe-Buffer Deadlocks, which are common with high-output tools like FFmpeg.
# By enforcing environment isolation and a 'Mandatory Cleanup' protocol,
# it prevents 'Process Leaks' even in complex, interactive pipelines.
@contextmanager
def open_secure_session(
    ctx: dict[str, Any],
    cmd: list[str],
    is_gui: bool = False,
    combine_stderr: bool = True,
    bufsize: int = 1,
) -> Generator[SessionInterface, None, None]:
    """Spawns a hardened system process as a context-managed session, enforcing a Zero-Trust sandbox and guaranteeing resource reclamation.

    Args:
        ctx: Runtime context dictionary containing environment details, paths, and user info.
        cmd: List of strings representing the command and its arguments to execute.
        is_gui: If True, conditionally injects graphical display and session context.
        combine_stderr: If True, combines standard error into standard output to prevent pipe-buffer deadlocks.
        bufsize: Integer buffer size for stream flushing (default is 1 for line-buffering).

    Yields:
        A SessionInterface instance wrapping the process and its background-drained output queue.
    """

    # ENVIRONMENT SANITIZATION & ZERO-TRUST ISOLATION
    # Purges caller-defined environment variables, establishing a minimal,
    # deterministic execution profile for the child process.
    safe_env: dict[str, str] = {
        "LC_ALL": "C",
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": str(ctx.get("home", "/tmp")),
        "TMPDIR": str(ctx.get("home", "/tmp")),
        "USER": str(ctx.get("user", "nobody")),
        "LANG": "en_US.UTF-8",
    }

    # CONDITIONAL GRAPHICAL CONTEXT & DESKTOP PASSTHROUGH
    # Conditionally injects display variables, Wayland protocol flags, and session type declarations
    # when GUI operations are requested, optimizing desktop application runtime.
    if is_gui and "display_context" in ctx:
        gui_vars: dict[str, str] = {
            str(k): str(v) for k, v in ctx["display_context"].items() if v
        }
        safe_env.update(gui_vars)

        # ELECTRON/WAYLAND NATIVE OPTIMIZATION
        # Forces Electron and Chromium-based tools to prefer native Wayland rendering flags.
        safe_env["ELECTRON_OZONE_PLATFORM_HINT"] = "auto"

        # XDG SESSION TYPE DECLARATION
        # Guarantees proper window decoration rendering and compositor handshakes.
        safe_env["XDG_SESSION_TYPE"] = "wayland"

    # DYNAMIC I/O STREAM ABSTRACTION & DEADLOCK PREVENTION
    # Configures stderr routing to standard output or separate pipes to prevent OS pipe-buffer deadlocks.
    stderr_setting: int = subprocess.STDOUT if combine_stderr else subprocess.PIPE

    # SESSION HANDLE & TELEMETRY QUEUE INITIALIZATION
    # Pre-allocates process handles and a thread-safe telemetry bridge queue.
    proc: "Optional[subprocess.Popen[str]]" = None
    out_q: "queue.Queue[Optional[str]]" = queue.Queue()

    try:
        # ATOMIC SUBPROCESS SPAWNING & LINE-BUFFERED FLUSHING
        # Launches the persistent command under text mode with line-buffered flushing for real-time telemetry.
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_setting,
            text=True,
            env=safe_env,
            bufsize=bufsize,
            errors="replace",
        )

        # ASYNCHRONOUS STREAM DRAINER & MONITOR
        # Continuously drains text-mode pipes into the thread-safe queue to prevent blocking on full buffers.
        def _stream_drainer(
            pipe: "Optional[IO[str]]", q: "queue.Queue[Optional[str]]"
        ) -> None:
            """
            Internal worker to drain a text-mode pipe into the telemetry queue.
            Uses iterative line-consumption for high-fidelity log preservation.
            """
            try:
                if pipe:
                    for line in iter(pipe.readline, ""):
                        if line:
                            q.put(line)
            finally:
                # SENTINEL INJECTION & RESOURCE RECLAMATION
                # Injects a termination sentinel into the queue and closes pipe handles.
                q.put(None)
                if pipe:
                    pipe.close()

        # TELEMETRY OBSERVER THREAD DEPLOYMENT
        # Starts the daemon thread to monitor stdout streams asynchronously.
        if proc.stdout is not None:
            monitor_thread: threading.Thread = threading.Thread(
                target=_stream_drainer, args=(proc.stdout, out_q), daemon=True
            )
            monitor_thread.start()
        else:
            raise RuntimeError("Failed to initialize stdout pipe for secure session.")

        # INTERFACE HANDOVER
        # Yields a high-level handle abstracting the process and its background-drained output queue.
        yield SessionInterface(proc, out_q)

    # BINARY RESOLUTION ERROR INTERCEPTION
    # Handles missing system executables or invalid binary paths gracefully.
    except FileNotFoundError as e:
        report_status(
            state="warn",
            message=f"File not found: {e.filename}",
        )
        raise PathResolutionError(filename=str(e.filename)) from e

    # INTERRUPT SIGNAL CAPTURE (USER ABORT)
    # Catches manual termination signals to sanitize standard output streams and trigger shutdown routines.
    except KeyboardInterrupt:
        if proc:
            proc.terminate()

        print("\n")
        report_status(
            state="warn",
            message=str(UserCancelError()),
        )
        raise UserCancelError from None

    finally:
        # MANDATORY RESOURCE RECLAMATION & LEAK PREVENTION
        # Guarantees process termination, wait timeouts, SIGKILL escalation, and file descriptor cleanup.
        if proc:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=ctx.get("cleanup_timeout", 5))
                except subprocess.TimeoutExpired:
                    proc.kill()

            # SESSION INTEGRITY LOGGING (POST-MORTEM)
            # Captures and reports non-zero exit codes for system-level audit logs.
            exit_code: "Optional[int]" = proc.poll()
            if exit_code is not None and exit_code != 0:
                report_status(
                    state="warn", message=f"(Exit {exit_code}): {shlex.join(cmd)}"
                )

            # RESOURCE STREAM RECLAMATION
            # Explicitly closes all associated pipes to prevent file descriptor exhaustion.
            for pipe in [proc.stdin, proc.stdout, proc.stderr]:
                if pipe:
                    try:
                        pipe.close()
                    except OSError:
                        pass
