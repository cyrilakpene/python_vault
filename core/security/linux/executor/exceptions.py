import shlex


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
