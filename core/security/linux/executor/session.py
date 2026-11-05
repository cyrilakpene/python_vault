import queue
import shlex
import subprocess
from contextlib import contextmanager
from typing import Any, Generator


from .drainer import start_stream_drainer  # type: ignore[import-not-found]
from .environment import build_safe_environment  # type: ignore[import-not-found]
from .exceptions import PathResolutionError, UserCancelError  # type: ignore[import-not-found]
from .interface import SessionInterface  # type: ignore[import-not-found]
from .streams import configure_session_streams  # type: ignore[import-not-found]
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# PROCESS MANAGEMENT SUBSYSTEM: HARDENED SESSION CONTEXT MANAGER
# This utility spawns a secure process session, sets up standard I/O streams,
# starts stream draining, and guarantees deterministic resource reclamation on exit.
# [>] EXECUTING SECURE SESSION SPAWNING & RESOURCE RECLAMATION
@contextmanager
def open_secure_session(
    ctx: dict[str, Any],
    cmd: list[str],
    combine_stderr: bool = True,
    bufsize: int = 1,
    stdin: Any = subprocess.PIPE,
) -> Generator[SessionInterface, None, None]:
    """
    Spawns a hardened process session and guarantees deterministic resource reclamation.

    Args:
        ctx (dict[str, Any]): Execution context dictionary.
        cmd (list[str]): Command list to execute.
        combine_stderr (bool): Flag indicating whether to combine stderr into stdout.
        bufsize (int): Buffer size for the process streams.
        stdin (Any): Standard input configuration.

    Returns:
        Generator[SessionInterface, None, None]: A generator yielding the active session interface.
    """
    # ENVIRONMENT SANITIZATION
    # Builds a secure execution environment dictionary based on the execution context.
    safe_env = build_safe_environment(ctx)

    proc: "subprocess.Popen[Any]|None" = None
    out_q: "queue.Queue[str | None]" = queue.Queue()

    # I/O STREAM CONFIGURATION
    # Configures standard input, output, and error streams based on combining options.
    actual_stdin, actual_stdout, actual_stderr = configure_session_streams(
        combine_stderr, stdin
    )

    try:
        # PROCESS SPAWNING & EXECUTION
        # Spawns the subprocess with text mode, environment buffers, and stream mappings.
        proc = subprocess.Popen(
            cmd,
            stdin=actual_stdin,
            stdout=actual_stdout,
            stderr=actual_stderr,
            text=True,
            env=safe_env,
            bufsize=bufsize,
            errors="replace",
        )

        # STREAM DRAINER INITIALIZATION
        # Starts background threads to drain process output streams into the thread-safe queue.
        start_stream_drainer(proc, out_q)

        # SESSION INTERFACE YIELD
        # Yields the active session interface wrapper containing the process and output queue.
        yield SessionInterface(proc, out_q)

    # FILE NOT FOUND EXCEPTION HANDLING
    # Catches missing binary errors and raises a custom PathResolutionError.
    except FileNotFoundError as e:
        report_status(
            state="warn",
            message=f"Path resolution error: Required file or binary not found -> {e.filename}",
            context=LogContext(
                component="security.executor",
                log_path=log_path,
                silent=False,
                trace_id="executor",
                actor=context.get("user"),
                exception=str(e),
                payload={
                    "error_type": "FileNotFoundError",
                    "filename": str(e.filename),
                },
            ),
        )
        raise PathResolutionError(filename=str(e.filename)) from e

    # KEYBOARD INTERRUPT EXCEPTION HANDLING
    # Gracefully terminates the running process upon receiving a user keyboard interrupt.
    except KeyboardInterrupt:
        if proc:
            proc.terminate()
        print("\n")
        report_status(
            state="warn",
            message=str(UserCancelError()),
            context=LogContext(
                component="security.executor",
                log_path=log_path,
                silent=False,
                trace_id="executor",
                actor=context.get("user"),
                exception=str(UserCancelError()),
                payload={
                    "error_type": "KeyboardInterrupt",
                    "reason": "user_interrupted_process",
                },
            ),
        )
        raise UserCancelError from None

    # DETERMINISTIC RESOURCE RECLAMATION (FINALLY BLOCK)
    # Guarantees cleanup of process termination, timeouts, exit code reporting, and pipe closures.
    finally:
        if proc:
            # PROCESS TERMINATION & TIMEOUT ENFORCEMENT
            # Terminates the process if still running, waiting up to the timeout before killing.
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=ctx.get("cleanup_timeout", 5))
                except subprocess.TimeoutExpired:
                    proc.kill()

            # EXIT CODE EVALUATION & WARNING REPORTING
            # Checks the final exit code and reports a warning if execution failed.
            exit_code: int | None = proc.poll()
            if exit_code is not None and exit_code != 0:
                report_status(
                    state="warn",
                    message=f"Secure session process execution failed with exit code {exit_code} -> {shlex.join(cmd)}",
                    context=LogContext(
                        component="security.executor",
                        log_path=log_path,
                        silent=False,
                        trace_id="executor",
                        actor=context.get("user"),
                        payload={
                            "error_type": "SessionProcessFailed",
                            "returncode": exit_code,
                            "command": shlex.join(cmd),
                        },
                    ),
                )

            # PIPE CLEANUP & CLOSURE
            # Safely closes all active standard pipes associated with the process.
            for pipe in [proc.stdin, proc.stdout, proc.stderr]:
                if pipe:
                    try:
                        pipe.close()
                    except OSError:
                        pass
