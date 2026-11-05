import re
import sys
from typing import Any, cast

from .constants import report_status, LogContext, context, log_path  # type: ignore[import-not-found]


# SYSTEM UTILITIES SUBSYSTEM: SUPPRESSION PATTERN COMPILATION
# This utility compiles user-defined string or regular expression suppression patterns
# into executable compiled regex Pattern objects for telemetry filtering.
# [>] EXECUTING PATTERN COMPILATION
def compile_suppression_patterns(
    suppress_patterns: list[str | re.Pattern[str]] | None,
) -> list[re.Pattern[str]]:
    """
    Compiles user-defined string or regex suppression patterns into executable Pattern objects.

    Args:
        suppress_patterns (list[str | re.Pattern[str]] | None): A list of raw strings or compiled regex patterns to process, or None.

    Returns:
        list[re.Pattern[str]]: A list of compiled regular expression Pattern objects.
    """
    # COMPILED COLLECTION INITIALIZATION
    # Initializes the collection container for compiled regular expression objects.
    compiled: list[re.Pattern[str]] = []

    # PATTERN ITERATION & COMPILATION
    # Iterates through provided suppression patterns, compiling raw strings into regex patterns
    # and preserving already-compiled pattern instances.
    if suppress_patterns:
        for pat in suppress_patterns:
            if isinstance(pat, str):
                compiled.append(re.compile(pat))
            else:
                compiled.append(pat)

    return compiled


# SYSTEM UTILITIES SUBSYSTEM: SUPPRESSION RANGE COMPILATION
# This utility compiles user-defined start and end boundary pattern pairs (strings or regex)
# into compiled regular expression tuples used for block-level output suppression.
# [>] EXECUTING RANGE PATTERN COMPILATION
def compile_suppression_ranges(
    suppress_ranges: list[tuple[str | re.Pattern[str], str | re.Pattern[str]]] | None,
) -> list[tuple[re.Pattern[str], re.Pattern[str]]]:
    """
    Compiles start and end boundary pairs into compiled regular expression tuples for block suppression.

    Args:
        suppress_ranges (list[tuple[str | re.Pattern[str], str | re.Pattern[str]]] | None):
            A list of start and end boundary pattern pairs, or None.

    Returns:
        list[tuple[re.Pattern[str], re.Pattern[str]]]: A list of compiled regex boundary tuples.
    """
    # COMPILED RANGE COLLECTION INITIALIZATION
    # Initializes the container for compiled regular expression boundary tuples.
    compiled: list[tuple[re.Pattern[str], re.Pattern[str]]] = []

    # RANGE PAIR ITERATION & COMPILATION
    # Iterates through provided suppression range pairs, compiling raw string patterns
    # into regex objects and preserving already-compiled patterns for both start and end boundaries.
    if suppress_ranges:
        for start_pat, end_pat in suppress_ranges:
            s_compiled = (
                re.compile(start_pat) if isinstance(start_pat, str) else start_pat
            )
            e_compiled = re.compile(end_pat) if isinstance(end_pat, str) else end_pat
            compiled.append((s_compiled, e_compiled))

    return compiled


# SYSTEM UTILITIES SUBSYSTEM: TELEMETRY FILTERING & LINE REDACTION
# This utility evaluates and filters single output lines against stateful suppression ranges
# and individual security patterns, managing prompt spacing and writing safe output to stdout.
# [>] EXECUTING LINE FILTERING & REDACTION
def filter_and_write_line(
    clean_line: str,
    compiled_patterns: list[re.Pattern[str]],
    compiled_ranges: list[tuple[re.Pattern[str], re.Pattern[str]]],
    state: dict[str, Any],
) -> None:
    """
    Evaluates suppression ranges and individual patterns on a single line, updates state, and writes to stdout.

    Args:
        clean_line (str): The sanitized text line of process output to evaluate.
        compiled_patterns (list[re.Pattern[str]]): A list of compiled regex patterns for individual line suppression.
        compiled_ranges (list[tuple[re.Pattern[str], re.Pattern[str]]]): A list of compiled range boundary tuples (start, end).
        state (dict[str, Any]): Mutable execution state dictionary tracking prompt history and active suppression ranges.

    Returns:
        None
    """
    # REDUNDANT PROMPT SPACING SUPPRESSION
    # Suppresses consecutive empty lines immediately following an interactive prompt.
    if state.get("last_was_prompt") and not clean_line:
        state["last_was_prompt"] = False
        return

    state["last_was_prompt"] = False
    active_range_idx = cast(int | None, state.get("active_range_idx"))

    # STATEFUL RANGE SUPPRESSION EVALUATION
    # Checks if currently inside a suppression range block; if so, tests for the end boundary pattern
    # to terminate the block, or continues suppressing the line.
    if active_range_idx is not None:
        _, end_pat = compiled_ranges[active_range_idx]
        if end_pat.search(clean_line):
            state["active_range_idx"] = None
        return
    else:
        # RANGE START DETECTION
        # Scans for any opening range pattern to initiate block-level suppression.
        for i, (start_pat, _) in enumerate(compiled_ranges):
            if start_pat.search(clean_line):
                state["active_range_idx"] = i
                sys.stdout.write("\r\n")
                report_status(
                    state="info",
                    message="Suppression filter triggered: PTY output block matched security range boundary.",
                    context=LogContext(
                        component="security.executor",
                        log_path=log_path,
                        silent=True,
                        trace_id="executor",
                        actor=context.get("user"),
                        payload={
                            "suppression_type": "range_block",
                            "range_index": i,
                        },
                    ),
                )
                return

    # INDIVIDUAL REGEX PATTERN EVALUATION PIPELINE
    # Evaluates the line against individual compiled suppression patterns, logging and filtering matches.
    for pattern in compiled_patterns:
        if pattern.search(clean_line):
            sys.stdout.write("\r\n")
            report_status(
                state="info",
                message="Suppression filter triggered: PTY output line matched security pattern.",
                context=LogContext(
                    component="security.executor",
                    log_path=log_path,
                    silent=True,
                    trace_id="executor",
                    actor=context.get("user"),
                    payload={
                        "suppression_type": "pattern_line",
                        "pattern": pattern.pattern,
                    },
                ),
            )
            return

    # PASSTHROUGH NON-SENSITIVE OUTPUT
    # Writes non-sensitive output lines directly to standard output and flushes the stream.
    sys.stdout.write(clean_line + "\r\n")
    sys.stdout.flush()


# SYSTEM UTILITIES SUBSYSTEM: CHUNK DATA PROCESSING & TELEMETRY BUFFERING
# This utility decodes raw byte chunks into text, buffers incoming lines, and delegates
# stream segments to the line-by-line filtering pipeline with interactive prompt detection.
# [>] EXECUTING CHUNK DATA PROCESSING
def process_chunk_data(
    chunk: bytes,
    compiled_patterns: list[re.Pattern[str]],
    compiled_ranges: list[tuple[re.Pattern[str], re.Pattern[str]]],
    state: dict[str, Any],
) -> None:
    """
    Decodes raw byte chunks, buffers text lines, and delegates line-by-line filtering.

    Args:
        chunk (bytes): The raw byte chunk received from the process stream.
        compiled_patterns (list[re.Pattern[str]]): A list of compiled regex patterns for individual line suppression.
        compiled_ranges (list[tuple[re.Pattern[str], re.Pattern[str]]]): A list of compiled range boundary tuples (start, end).
        state (dict[str, Any]): Mutable execution state dictionary tracking line buffers, prompt history, and active ranges.

    Returns:
        None
    """
    # CHUNK VALIDATION & DECODING
    # Returns immediately if the chunk is empty; otherwise, decodes raw bytes into UTF-8 text with error replacement.
    if not chunk:
        return

    text = chunk.decode("utf-8", errors="replace")

    # FAST-PATH UNFILTERED STREAMING
    # Bypasses buffering and filtering overhead if no suppression patterns or ranges are registered,
    # normalizes line endings, and writes directly to standard output.
    if not compiled_patterns and not compiled_ranges:
        normalized = text.replace("\r\n", "\n").replace("\n", "\r\n")
        sys.stdout.write(normalized)
        sys.stdout.flush()
        return

    # BUFFER ACCUMULATION & LINE EXTRACTION
    # Appends decoded text to the persistent line buffer and extracts complete lines delimited by newline characters,
    # delegating each line to the filtering and writing pipeline.
    state["line_buffer"] = state.get("line_buffer", "") + text

    while "\n" in state["line_buffer"]:
        idx = state["line_buffer"].find("\n")
        line = state["line_buffer"][:idx]
        state["line_buffer"] = state["line_buffer"][idx + 1 :]
        filter_and_write_line(line, compiled_patterns, compiled_ranges, state)

    # PROMPT DETECTION & TRAILING BUFFER FLUSH
    # Inspects any remaining buffered content for trailing interactive prompt indicators (such as colons or question marks),
    # flushes them through the filter, and updates prompt tracking state.
    if state["line_buffer"]:
        stripped = state["line_buffer"].rstrip()
        if stripped.endswith(":") or stripped.endswith("?"):
            filter_and_write_line(
                state["line_buffer"], compiled_patterns, compiled_ranges, state
            )
            state["last_was_prompt"] = True
            state["line_buffer"] = ""
