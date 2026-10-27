import sys
import subprocess
from typing import Any, TextIO


# SYSTEM UTILITIES SUBSYSTEM: ATOMIC SUBPROCESS STREAM CONFIGURATION
# This utility configures standard output and error stream configurations for atomic
# command execution, handling capture pipes, silent mode suppression, and default inheritance.
# [>] CONFIGURING ATOMIC SUBPROCESS STREAMS
def configure_run_streams(
    capture_output: bool,
    silent: bool,
) -> tuple[int | None | TextIO, int | None | TextIO]:
    """
    Configures standard output and error streams for atomic command execution.

    Args:
        capture_output (bool): If True, captures both stdout and stderr into pipes.
        silent (bool): If True, suppresses stdout by routing it to DEVNULL and stderr to sys.stderr.

    Returns:
        tuple[int | None | TextIO, int | None | TextIO]: A tuple containing configured stdout and stderr settings.
    """
    # INITIAL STREAM SETTINGS
    # Initializes output and error stream settings to default inherit values.
    stdout_setting: int | None | TextIO = None
    stderr_setting: int | None | TextIO = None

    # CONDITIONAL EXECUTION MODE ROUTING
    # Evaluates execution flags to assign capture pipes, DEVNULL suppression, or inheritance defaults.
    if capture_output:
        stdout_setting = subprocess.PIPE
        stderr_setting = subprocess.PIPE
    elif silent:
        stdout_setting = subprocess.DEVNULL
        stderr_setting = sys.stderr
    else:
        stdout_setting = None
        stderr_setting = None

    return stdout_setting, stderr_setting


# SYSTEM UTILITIES SUBSYSTEM: I/O STREAM ROUTING & CONFIGURATION
# This utility configures standard input, output, and error streams for continuous process execution,
# supporting optional redirection of standard error into standard output.
# [>] EXECUTING SESSION STREAM SETUP
def configure_session_streams(
    combine_stderr: bool,
    stdin: Any,
) -> tuple[Any, Any, Any]:
    """
    Configures standard input, output, and error streams for continuous process execution.

    Args:
        combine_stderr (bool): Flag indicating whether to redirect stderr into stdout.
        stdin (Any): The input stream or data source to route to the process.

    Returns:
        tuple[Any, Any, Any]: A tuple containing configured stdin, stdout, and stderr streams.
    """
    # STANDARD STREAM ROUTING CONFIGURATION
    # Configures standard input, standard output pipe, and conditional stderr redirection into stdout.
    actual_stdin = stdin
    actual_stdout = subprocess.PIPE
    actual_stderr = subprocess.STDOUT if combine_stderr else subprocess.PIPE

    return actual_stdin, actual_stdout, actual_stderr
