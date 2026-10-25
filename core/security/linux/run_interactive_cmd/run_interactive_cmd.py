import errno
import os
import pty
import re
import select
import shlex
import subprocess
import sys
import termios
import time
import tty
from typing import Any

from interface.report_status import report_status  # type: ignore[import-not-found]
from security.runtime_context import log_path  # type: ignore[import-not-found]


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


# STREAM TEXT ACCUMULATOR & REGEX SUPPRESSION ENGINE
# Manages line-buffered streaming output across PTY chunk boundaries, detecting sensitive output
# matching configured suppression rules or multi-line block ranges, suppressing matched lines silently
# from live terminal displays, and logging occurrences via report_status() while preserving complete output history in memory.
class TextAccumulator:
    """Buffers live PTY byte chunks into text lines to evaluate sensitive pattern rules
    and multi-line suppression ranges, silently suppressing matching output from sys.stdout while logging events.
    """

    def __init__(
        self,
        suppress_patterns: list[str | re.Pattern[str]] | None = None,
        suppress_ranges: (
            list[tuple[str | re.Pattern[str], str | re.Pattern[str]]] | None
        ) = None,
    ):
        # REGEX PATTERN COMPILATION
        # Compiles user-defined string or regex suppression patterns into executable Pattern objects for individual lines.
        self.compiled_patterns: list[re.Pattern[str]] = []
        if suppress_patterns:
            for pat in suppress_patterns:
                if isinstance(pat, str):
                    self.compiled_patterns.append(re.compile(pat))
                else:
                    self.compiled_patterns.append(pat)

        # RANGE PATTERN COMPILATION
        # Compiles start and end boundary pairs into compiled regular expression tuples for multi-line block suppression.
        self.compiled_ranges: list[tuple[re.Pattern[str], re.Pattern[str]]] = []
        if suppress_ranges:
            for start_pat, end_pat in suppress_ranges:
                s_compiled = (
                    re.compile(start_pat) if isinstance(start_pat, str) else start_pat
                )
                e_compiled = (
                    re.compile(end_pat) if isinstance(end_pat, str) else end_pat
                )
                self.compiled_ranges.append((s_compiled, e_compiled))

        self.line_buffer = ""

        # RANGE SUPPRESSION STATE TRACKER
        # Tracks the index of the currently active suppression block range, or None if no range block is open.
        self.active_range_idx: int | None = None

        # PROMPT SPACING STATE TRACKER
        # Tracks whether the last flushed output was an interactive prompt, preventing redundant empty lines upon user Enter keystrokes.
        self.last_was_prompt: bool = False

    def process_bytes(self, chunk: bytes) -> None:
        """Processes raw byte chunks from PTY master, buffering text lines to evaluate
        suppression regexes and ranges before echoing cleared lines to live stdout.
        """
        if not chunk:
            return

        # DECODE BYTE STREAM TO TEXT
        # Converts incoming PTY bytes into UTF-8 strings, replacing invalid surrogate sequences safely.
        text = chunk.decode("utf-8", errors="replace")

        # FAST-PATH ZERO-OVERHEAD STREAMING
        # Writes directly to stdout if no individual patterns or range rules are registered, normalizing line endings for raw terminals.
        if not self.compiled_patterns and not self.compiled_ranges:
            normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
            sys.stdout.write(normalized)
            sys.stdout.flush()
            return

        # ACCUMULATE STREAM CHUNKS
        # Append incoming text chunk to the persistent line buffer for multi-chunk inspection.
        self.line_buffer += text

        # LINE-BUFFERED MULTI-CHUNK EVALUATION
        # Extracts complete lines delimited strictly by newlines (\n) to prevent carriage return layout fragmentation.
        while "\n" in self.line_buffer:
            # DELIMITER SEARCH SCAN
            # Locates the first standard newline terminator within the current accumulation buffer.
            idx = self.line_buffer.find("\n")

            # EXTRACT COMPLETE LINE SEGMENT
            # Slice the buffer up to the newline character.
            line = self.line_buffer[:idx]

            # ADVANCE ACCUMULATOR BUFFER POINTER
            # Removes the processed line and its newline terminator from the active working buffer.
            self.line_buffer = self.line_buffer[idx + 1 :]
            self._write_filtered_line(line)

        # PROMPT STALL PREVENTION CHECK
        # Interactive prompts (e.g., 'Password: ', 'Repeat: ') often terminate with a colon or question mark
        # without a trailing newline. Flush them immediately to guarantee real-time terminal interactivity.
        if self.line_buffer:
            stripped = self.line_buffer.rstrip()
            if stripped.endswith(":") or stripped.endswith("?"):
                self._write_filtered_line(self.line_buffer)
                self.last_was_prompt = (
                    True  # Mark that a prompt was just explicitly flushed
                )
                self.line_buffer = ""

    def flush(self) -> None:
        """Flushes any remaining trailing buffer contents upon child process exit."""
        if self.line_buffer:
            self._write_filtered_line(self.line_buffer)
            self.line_buffer = ""
            sys.stdout.flush()

    def _write_filtered_line(self, raw_line: str) -> None:
        # CLEAN LINE TERMINATION
        # Strips trailing carriage returns to prevent duplicate control characters or misalignment in raw terminal mode.
        clean_line = raw_line.rstrip("\r")

        # REDUNDANT PROMPT SPACING SUPPRESSION
        # If an interactive prompt was just flushed without a trailing newline, the user pressing Enter generates
        # an immediate empty line chunk. Suppress this redundant empty line to keep prompts cleanly adjacent.
        if self.last_was_prompt and not clean_line:
            self.last_was_prompt = False
            return

        # RESET PROMPT FLAG ON NON-EMPTY LINES
        self.last_was_prompt = False

        # STATEFUL RANGE SUPPRESSION EVALUATION
        # Evaluates whether we are currently inside a multi-line suppression block or if a new range start pattern is met.
        if self.active_range_idx is not None:
            start_pat, end_pat = self.compiled_ranges[self.active_range_idx]

            # CHECK RANGE TERMINATION BOUNDARY
            # Evaluates if the current line matches the closing boundary pattern of the active block.
            if end_pat.search(clean_line):
                self.active_range_idx = (
                    None  # Reset state block tracker once closing line is processed
                )

            # SILENT INTERMEDIATE SUPPRESSION
            # Drops lines falling within the active block range silently without duplicate log spamming.
            return
        else:
            # SCAN FOR RANGE START TRIGGERS
            # Checks if the current line triggers the beginning of any registered multi-line suppression range.
            for i, (start_pat, end_pat) in enumerate(self.compiled_ranges):
                if start_pat.search(clean_line):
                    self.active_range_idx = i

                    # ENSURE CLEAN LINE SEPARATION IN RAW MODE
                    # Forces a fresh line reset before printing the audit notification message to prevent horizontal offset shifts.
                    sys.stdout.write("\r\n")

                    # TELEMETRY LOGGING
                    # Registers the security suppression event once per suppressed block range.
                    report_status(
                        state="info",
                        message="Suppressed sensitive PTY output block matching security pattern.",
                        silent=True,
                        log_path=log_path,
                    )
                    return

        # INDIVIDUAL REGEX PATTERN EVALUATION PIPELINE
        # Checks the current line against all individual registered suppression patterns.
        for pattern in self.compiled_patterns:
            if pattern.search(clean_line):
                # ENSURE CLEAN LINE SEPARATION IN RAW MODE
                # Resets cursor position to column zero before writing telemetry notice.
                sys.stdout.write("\r\n")

                # SILENT STREAM SUPPRESSION & TELEMETRY LOGGING
                # Suppresses sensitive terminal output from live display and registers audit entry.
                report_status(
                    state="info",
                    message="Suppressed sensitive PTY output line matching security pattern.",
                    silent=True,
                    log_path=log_path,
                )
                return

        # PASSTHROUGH NON-SENSITIVE OUTPUT
        # Writes non-matching output lines directly to live console standard output with carriage return and newline for raw mode.
        sys.stdout.write(clean_line + "\r\n")
        sys.stdout.flush()


# ARCHITECTURAL GATEKEEPER: INTERACTIVE PTY SUBPROCESS EXECUTION SANDBOX
# Parallel companion to run_secure_cmd() designed for interactive tools (like gocryptfs init)
# that require a real pseudo-terminal (isatty) to reveal sensitive output like master keys,
# while maintaining zero-trust environment isolation, regex/range stream suppression, and live stream capture.
def run_interactive_cmd(
    ctx: dict[str, Any],
    cmd: list[str],
    timeout: int | None = None,
    is_gui: bool = False,
    suppress_patterns: list[str | re.Pattern[str]] | None = None,
    suppress_ranges: (
        list[tuple[str | re.Pattern[str], str | re.Pattern[str]]] | None
    ) = None,
    max_buffer_bytes: int = 10_485_760,  # 10MB safety ceiling
) -> tuple[int, str]:
    """Executes an interactive command within a hardened PTY environment, allowing terminal prompts
    while capturing output streams and selectively suppressing sensitive output patterns or ranges from live terminal display.

    Args:
        ctx: Runtime context dictionary containing environment details, paths, and user info.
        cmd: List of strings representing the command and its arguments to execute.
        timeout: Optional timeout duration in seconds for the command execution.
        is_gui: If True, conditionally injects graphical display and session context.
        suppress_patterns: Optional list of regex patterns or strings to filter individual lines from live stdout display.
        suppress_ranges: Optional list of start/end pattern tuples to suppress multi-line output blocks.
        max_buffer_bytes: Maximum allowed bytes to accumulate in memory to prevent OOM.

    Returns:
        A tuple containing (exit_code, captured_output_string).
    """
    master_fd: int | None = None
    slave_fd: int | None = None
    proc: subprocess.Popen[Any] | None = None
    captured_byte_buffer = bytearray()
    old_tty_settings = None

    # LIVE STREAM FILTER INITIALIZATION
    # Instantiates the line-buffered stream accumulator with both line patterns and multi-line block ranges
    # to inspect PTY stdout chunks in real-time and suppress matching sensitive data before writing to the physical console.
    accumulator = TextAccumulator(
        suppress_patterns=suppress_patterns,
        suppress_ranges=suppress_ranges,
    )

    try:
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
            "TERM": "xterm-256color",
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

        # PTY ALLOCATION & TERMINAL EMULATION GATEWAY
        # Opens a pseudo-terminal pair. The slave file descriptor acts as the process's standard streams,
        # successfully satisfying isatty() checks so tools like gocryptfs reveal sensitive output like master keys.
        master_fd, slave_fd = pty.openpty()

        # DISABLE PTY LOCAL ECHO ON SLAVE DESCRIPTOR
        # Clears the ECHO flag in terminal local control attributes so typed keystrokes (such as passwords)
        # are not automatically mirrored back into the output stream by the kernel PTY driver.
        try:
            slave_attrs = termios.tcgetattr(slave_fd)
            slave_attrs[
                3
            ] &= ~termios.ECHO  # Index 3 corresponds to local flags (lflags)
            termios.tcsetattr(slave_fd, termios.TCSANOW, slave_attrs)
        except termios.error:
            pass

        # RAW TERMINAL MODE SETUP FOR LIVE INTERACTION
        # Puts standard input into raw mode to stream unbuffered keystrokes directly to the PTY master descriptor.
        if sys.stdin.isatty():
            try:
                old_tty_settings = termios.tcgetattr(sys.stdin)
                tty.setraw(sys.stdin.fileno())
            except termios.error:
                old_tty_settings = None

        # ATOMIC SUBPROCESS SPAWNING WITH PTY
        # Launches the process bound to the PTY slave descriptor under strict isolation and session detachment.
        proc = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            env=safe_env,
            start_new_session=True,
            text=False,
        )

        # SLAVE DESCRIPTOR RECLAMATION
        # Closes the slave file descriptor in the parent process so EOF is correctly received when the child process exits.
        os.close(slave_fd)
        slave_fd = None

        # NON-BLOCKING I/O MULTIPLEXING LOOP (SELECT WATCHDOG)
        # Bridges user keyboard input from standard input to the PTY master while simultaneously draining
        # and recording all terminal output into memory buffer chunks for subsequent parsing and screen clearing.
        start_time = time.time()

        while True:
            # EXECUTION TIMEOUT EVALUATION
            # Checks if cumulative runtime has exceeded the specified threshold.
            if timeout is not None and (time.time() - start_time) > timeout:
                proc.terminate()
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

            # PROCESS TERMINATION POLL CHECK
            # Evaluates if the child process has completed execution.
            if proc.poll() is not None:
                # BUFFER DRAIN FLUSH
                # Drains any remaining buffered output data from the PTY master file descriptor before exiting loop.
                try:
                    if master_fd is not None:
                        r, _, _ = select.select([master_fd], [], [], 0.1)
                        if master_fd in r:
                            data = os.read(master_fd, 4096)
                            if data:
                                if (
                                    len(captured_byte_buffer) + len(data)
                                    <= max_buffer_bytes
                                ):
                                    captured_byte_buffer.extend(data)
                                accumulator.process_bytes(data)
                except OSError as e:
                    if e.errno != errno.EIO:
                        pass
                break

            # I/O STREAM MULTIPLEXING VIA SELECT
            # Monitors standard input and PTY master descriptor for readability without blocking thread execution.
            watch_fds = [sys.stdin]
            if master_fd is not None:
                watch_fds.append(master_fd)

            r_list, _, _ = select.select(watch_fds, [], [], 0.1)

            # PTY MASTER READ PIPELINE
            # Captures output generated by the child process, recording chunks and processing them live through the accumulator.
            if master_fd and master_fd in r_list:
                try:
                    data = os.read(master_fd, 4096)
                    if not data:
                        break
                    if len(captured_byte_buffer) + len(data) <= max_buffer_bytes:
                        captured_byte_buffer.extend(data)
                    accumulator.process_bytes(data)
                except OSError as e:
                    # EIO indicates PTY child process closed slave descriptor upon exit
                    if e.errno == errno.EIO:
                        break
                    break

            # STANDARD INPUT WRITE PIPELINE
            # Forwards live keyboard strokes from the user directly into the interactive PTY session.
            if sys.stdin in r_list:
                try:
                    user_input = os.read(sys.stdin.fileno(), 1024)
                    if user_input and master_fd is not None:
                        os.write(master_fd, user_input)
                except OSError:
                    pass

        # STREAM ACCUMULATOR FLUSH
        # Flushes any trailing buffered line content to stdout before exiting command execution.
        accumulator.flush()

        # PROCESS SYNCHRONIZATION & EXIT CODE RECLAMATION
        # Blocks safely until the process completely terminates to guarantee accurate status code retrieval.
        exit_code = proc.wait()
        full_output = captured_byte_buffer.decode("utf-8", errors="replace")

        # EXIT STATUS VALIDATION
        # Raises a process failure error if the command exits with a non-zero status code.
        if exit_code != 0:
            report_status(
                state="warn",
                message=f"(Exit {exit_code}): {shlex.join(cmd)}",
                log_path=log_path,
            )
            raise subprocess.CalledProcessError(returncode=exit_code, cmd=cmd)

        return exit_code, full_output

    # TIMEOUT EXCEPTION INTERCEPTION
    # Intercepts expired process execution runtimes, logging critical warnings and raising
    # structured timeout exceptions to upstream handlers.
    except subprocess.TimeoutExpired as e:
        report_status(
            state="warn",
            message=f"Command killed after {e.timeout}s -> {shlex.join(e.cmd)}",
            log_path=log_path,
        )
        raise CommandTimeoutError(timeout=e.timeout, cmd=e.cmd) from e

    # PROCESS FAILURE EXCEPTION INTERCEPTION
    # Captures non-zero exit codes returned by system binaries, registering process state failures
    # and propagating custom execution exceptions.
    except subprocess.CalledProcessError as e:
        raise CommandFailedError(returncode=e.returncode, cmd=e.cmd) from e

    # BINARY RESOLUTION ERROR INTERCEPTION
    # Handles missing system executables or invalid binary paths gracefully by logging targets
    # and mapping them to standard filesystem error protocols.
    except FileNotFoundError as e:
        report_status(
            state="warn", message=f"File not found: {e.filename}", log_path=log_path
        )
        raise PathResolutionError(filename=str(e.filename)) from e

    # INTERRUPT SIGNAL CAPTURE (USER ABORT)
    # Catches manual termination signals (SIGINT/KeyboardInterrupt) to sanitize standard output streams
    # and trigger clean pipeline shutdown routines.
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        report_status(state="warn", message=str(UserCancelError()), log_path=log_path)
        raise UserCancelError from None

    finally:
        # RESTORE TERMINAL COOKED MODE
        # Guarantees standard input settings are restored to canonical/cooked line-buffered mode on exit.
        if old_tty_settings is not None and sys.stdin.isatty():
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty_settings)
            except termios.error:
                pass

        # MANDATORY RESOURCE RECLAMATION & FILE DESCRIPTOR CLEANUP
        # Ensures that PTY file descriptors are closed, memory buffer is zeroed out,
        # and active zombie processes are terminated or killed.
        if master_fd is not None:
            try:
                os.close(master_fd)
            except OSError:
                pass
        if slave_fd is not None:
            try:
                os.close(slave_fd)
            except OSError:
                pass
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

        # HEAP BUFFER ZEROING
        # Overwrites underlying bytes in mutable bytearray memory before exit.
        for i in range(len(captured_byte_buffer)):
            captured_byte_buffer[i] = 0
