import sys
from typing import TextIO

# LOCALIZED SYMBOLIC MAPPING: ENCAPSULATED STATUS INDICATORS
# We define the status indicators within the function scope to enforce
# encapsulation. This ensures the 'Business Logic' of the reporter
# remains self-contained and prevents unintended side-effects in
# the broader application state.
STATUS_MAP: dict[str, str] = {
    "task": "[>]",
    "info": "[~]",
    "log_info": " [~]",
    "warn": "[!]",
    "item": "  [-]",
    "done": "[+]",
    "fail": "[x]",
    "input": "[?]",
    "debug": " [d]",
    "proc": "[*]",
}


# SYMBOL RESOLUTION & STATUS MAPPING ENGINE
# This utility normalizes execution states and maps them to corresponding visual display symbols
# and persistent log representations using predefined status lookup tables.
# [>] EXECUTING SYMBOL RESOLUTION
def resolve_symbols(state: str) -> tuple[str, str, str]:
    """
    Resolves symbolic mappings, display strings, and log representations.

    Args:
        state: Raw status string or execution state identifier.

    Returns:
        tuple[str, str, str]: A tuple containing the normalized state string,
            the UI display symbol, and the log representation symbol.
    """
    # STATE NORMALIZATION
    # Safely converts the input state string to lowercase, handling potential None values
    # to ensure robust status map lookups.
    normalized_state = str(state or "").lower()

    # DISPLAY SYMBOL RESOLUTION
    # Maps the normalized state to an appropriate visual display symbol, translating 'log_info'
    # keys to standard info glyphs while falling back to a default empty bracket if unrecognized.
    display_key = "info" if normalized_state == "log_info" else normalized_state
    display_symbol: str = STATUS_MAP.get(display_key, "[ ]")

    # LOG SYMBOL RESOLUTION
    # Resolves the dedicated log symbol counterpart, mapping info keys to log-specific representations
    # and falling back to the display symbol if no unique log mapping exists.
    log_key = "log_info" if normalized_state == "info" else normalized_state
    log_symbol: str = STATUS_MAP.get(log_key, display_symbol)

    # SYMBOL MANIFEST RETURN
    # Returns the normalized state alongside its mapped display and log symbols.
    return normalized_state, display_symbol, log_symbol


# TERMINAL OUTPUT & STREAM ROUTING ENGINE
# This utility manages terminal rendering, handling verbosity filters, silence gates,
# and smart stream routing between stdout and stderr based on execution status.
# [>] EXECUTING TERMINAL OUTPUT RENDER
def render_output(
    message: str,
    display_symbol: str,
    normalized_state: str,
    stream: TextIO | None,
    is_verbose: bool,
    silent: bool,
) -> None:
    """
    Handles verbosity, silence gates, smart stream routing (stdout vs stderr), and terminal rendering.

    Args:
        message: The message string to render to the active output stream.
        display_symbol: The visual symbol or icon associated with the execution state.
        normalized_state: The normalized status string determining stream routing rules.
        stream: Optional override output stream object (defaults to stdout or stderr).
        is_verbose: Boolean flag indicating whether verbose diagnostic output is enabled.
        silent: Boolean flag indicating whether normal output should be suppressed.
    """
    # DEBUG VERBOSITY CHECK
    # Suppresses debug-level output unless verbose logging mode is explicitly enabled.
    if normalized_state == "debug" and not is_verbose:
        return

    # SILENCE GATE CHECK
    # Bails out early if silence mode is active and verbose mode is disabled.
    if silent and not is_verbose:
        return

    # SMART STREAM ROUTING RESOLUTION
    # Dynamically routes warning and failure states to stderr while sending standard output to stdout,
    # respecting any explicit stream overrides.
    if stream is None:
        stream = sys.stderr if normalized_state in ["warn", "fail"] else sys.stdout

    # TERMINAL RENDER & STREAM FLUSH
    # Prints the formatted symbol and message string to the resolved stream with immediate buffer flushing.
    print(f"{display_symbol} {message}", file=stream, flush=True)
