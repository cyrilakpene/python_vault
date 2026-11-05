import shlex
import subprocess
from typing import Any

from .environment import build_safe_environment  # type: ignore[import-not-found]
from .streams import configure_run_streams  # type: ignore[import-not-found]
from .exceptions import (
    CommandFailedError,  # type: ignore[import-not-found]
    CommandTimeoutError,  # type: ignore[import-not-found]
    PathResolutionError,  # type: ignore[import-not-found]
    UserCancelError,  # type: ignore[import-not-found]
)
from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# ARCHITECTURAL GATEKEEPER: HARDENED SUBPROCESS EXECUTION SANDBOX
# This engine provides a high-integrity abstraction layer for system commands.
# By enforcing environment isolation, resource timeouts, and standardized
# signal handling, it prevents 'Process Leaks' or unauthorized environment
# inheritance, ensuring that system calls remain deterministic and secure.
def run_secure_cmd(
    ctx: dict[str, Any],
    cmd: list[str],
    input_data: str | None = None,
    check: bool = True,
    capture_output: bool = False,
    silent: bool = True,
    timeout: int | None = None,
    is_gui: bool = False,
) -> subprocess.CompletedProcess[Any] | None:
    """Executes system commands within a hardened environment, enforcing isolation and resource watchdogs.

    Args:
        ctx: Runtime context dictionary containing environment details, paths, and user info.
        cmd: List of strings representing the command and its arguments to execute.
        input_data: Optional string input passed to the standard input stream of the process.
        check: If True, raises an exception on non-zero exit codes.
        capture_output: If True, captures standard output and standard error streams.
        silent: If True, suppresses standard output by directing it to DEVNULL.
        timeout: Optional timeout duration in seconds for the command execution.
        is_gui: If True, conditionally injects graphical display and session context.

    Returns:
        A CompletedProcess instance containing execution results, or None under specific routing.
    """
    try:
        # DYNAMIC I/O STREAM ABSTRACTION & ROUTING
        # Resolves process output routing based on execution flags via dedicated stream helper.
        stdout_setting, stderr_setting = configure_run_streams(capture_output, silent)

        # ENVIRONMENT SANITIZATION & ZERO-TRUST ISOLATION
        # Establishes a minimal, deterministic execution profile via centralized environment builder.
        safe_env = build_safe_environment(ctx, is_gui=is_gui)

        # ATOMIC SUBPROCESS EXECUTION & RESOURCE WATCHDOG
        # Invokes the system process driver under strict text-protocol isolation and timeout thresholds,
        # ensuring reliable signal handoffs and preventing zombie execution loops.
        return subprocess.run(
            cmd,
            input=input_data,
            check=check,
            stdout=stdout_setting,
            stderr=stderr_setting,
            text=True,
            env=safe_env,
            timeout=timeout,
        )

    # TIMEOUT EXCEPTION INTERCEPTION
    # Intercepts expired process execution runtimes, logging critical warnings and raising
    # structured timeout exceptions to upstream handlers.
    except subprocess.TimeoutExpired as e:
        report_status(
            state="warn",
            message=f"Execution timeout: Command terminated after {e.timeout}s -> {shlex.join(e.cmd)}",
            context=LogContext(
                component="security.executor",
                log_path=log_path,
                silent=False,
                trace_id="executor",
                actor=context.get("user"),
                exception=str(e),
                payload={
                    "error_type": "TimeoutExpired",
                    "timeout_seconds": e.timeout,
                    "command": shlex.join(e.cmd),
                },
            ),
        )
        raise CommandTimeoutError(timeout=e.timeout, cmd=e.cmd) from e

    # PROCESS FAILURE EXCEPTION INTERCEPTION
    # Captures non-zero exit codes returned by system binaries, registering process state failures
    # and propagating custom execution exceptions.
    except subprocess.CalledProcessError as e:
        report_status(
            state="warn",
            message=f"Command execution failed with exit code {e.returncode} -> {shlex.join(e.cmd)}",
            context=LogContext(
                component="security.executor",
                log_path=log_path,
                silent=False,
                trace_id="executor",
                actor=context.get("user"),
                exception=str(e),
                payload={
                    "error_type": "CalledProcessError",
                    "returncode": e.returncode,
                    "command": shlex.join(e.cmd),
                },
            ),
        )
        raise CommandFailedError(returncode=e.returncode, cmd=e.cmd) from e

    # BINARY RESOLUTION ERROR INTERCEPTION
    # Handles missing system executables or invalid binary paths gracefully by logging targets
    # and mapping them to standard filesystem error protocols.
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

    # INTERRUPT SIGNAL CAPTURE (USER ABORT)
    # Catches manual termination signals (SIGINT/KeyboardInterrupt) to sanitize standard output streams
    # and trigger clean pipeline shutdown routines.
    except KeyboardInterrupt:
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
