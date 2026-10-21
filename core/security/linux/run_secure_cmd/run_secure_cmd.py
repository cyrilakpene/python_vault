import subprocess
import sys
import shlex
from typing import Any, TextIO

from report_status import report_status  # type: ignore[import-not-found]


# SYSTEM TIMEOUT EXCEPTION CLASS
# Custom exception domain class used to signal when a subprocess command exceeds its allocated execution time limit.
# Standardizes timeout formatting across CLI workflows to enable graceful handling without raw stack traces.
class CommandTimeoutError(Exception):
    """Raised when a subprocess command times out."""

    def __init__(
        self,
        timeout: float,
        cmd: list[str] | str,
        message: str = "Command execution timed out.",
    ):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes timeout message with standard system tag, duration, and command details before delegating to BaseException initializer.
        formatted_cmd = shlex.join(cmd) if isinstance(cmd, list) else str(cmd)
        super().__init__(
            f"Operation Timeout: {message} (Limit: {timeout}s) -> {formatted_cmd}"
        )
        self.timeout = timeout
        self.cmd = cmd


# SYSTEM PROCESS FAILURE EXCEPTION CLASS
# Custom exception domain class used to signal when a subprocess command exits with a non-zero status code.
# Standardizes process failure formatting across CLI workflows to enable graceful handling without raw stack traces.
class CommandFailedError(Exception):
    """Raised when a subprocess command returns a non-zero exit status."""

    def __init__(
        self,
        returncode: int,
        cmd: list[str] | str,
        message: str = "Command execution failed.",
    ):
        # DOMAIN EXCEPTION FORMATTING
        # Prefixes failure message with standard system tag, exit code, and command details before delegating to BaseException initializer.
        formatted_cmd = shlex.join(cmd) if isinstance(cmd, list) else str(cmd)
        super().__init__(
            f"Operation Failed: {message} (Exit {returncode}) -> {formatted_cmd}"
        )
        self.returncode = returncode
        self.cmd = cmd


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
        # Resolves process output routing based on execution flags, directing verbose streams
        # to null devices or capture pipes to prevent log pollution while retaining real-time error handles.
        stdout_setting: int | None | TextIO = None
        stderr_setting: int | None | TextIO = None

        if capture_output:
            stdout_setting = subprocess.PIPE
            stderr_setting = subprocess.PIPE
        elif silent:
            stdout_setting = subprocess.DEVNULL
            stderr_setting = sys.stderr
        else:
            stdout_setting = None
            stderr_setting = None

        # ENVIRONMENT SANITIZATION & ZERO-TRUST ISOLATION
        # Purges caller-defined environment variables such as global paths and local homes,
        # establishing a deterministic, minimal execution profile to prevent environment hijacking
        # and unexpected binary behaviors.
        safe_env: dict[str, str] = {
            "LC_ALL": "C",
            "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME": ctx.get("home", "/tmp"),
            "USER": ctx.get("user", "nobody"),
            "LANG": "en_US.UTF-8",
        }

        # CONDITIONAL GRAPHICAL CONTEXT & DESKTOP PASSTHROUGH
        # Conditionally injects display variables, Wayland protocol flags, and session type declarations
        # when GUI operations are requested, optimizing desktop application runtime without compromising
        # system CLI integrity.
        if is_gui and "display_context" in ctx:
            gui_vars = {k: v for k, v in ctx["display_context"].items() if v}
            safe_env.update(gui_vars)

            # ELECTRON/WAYLAND NATIVE OPTIMIZATION
            # Forces Electron and Chromium-based tools to prefer native Wayland rendering flags
            # without bloating the primary command argument vector.
            safe_env["ELECTRON_OZONE_PLATFORM_HINT"] = "auto"

            # XDG SESSION TYPE DECLARATION
            # Guarantees proper window decoration rendering and compositor handshakes under
            # native Wayland protocol environments.
            safe_env["XDG_SESSION_TYPE"] = "wayland"

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
            message=f"Command killed after {e.timeout}s -> {shlex.join(e.cmd)}",
        )
        raise CommandTimeoutError(timeout=e.timeout, cmd=e.cmd) from e

    # PROCESS FAILURE EXCEPTION INTERCEPTION
    # Captures non-zero exit codes returned by system binaries, registering process state failures
    # and propagating custom execution exceptions.
    except subprocess.CalledProcessError as e:
        report_status(
            state="warn", message=f"(Exit {e.returncode}): {shlex.join(e.cmd)}"
        )
        raise CommandFailedError(returncode=e.returncode, cmd=e.cmd) from e

    # BINARY RESOLUTION ERROR INTERCEPTION
    # Handles missing system executables or invalid binary paths gracefully by logging targets
    # and mapping them to standard filesystem error protocols.
    except FileNotFoundError as e:
        report_status(
            state="warn",
            message=f"File not found: {e.filename}",
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
        )
        raise UserCancelError from None
